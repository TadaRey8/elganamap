# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import sqlite3
import os
import json
import requests
import traceback
from dotenv import load_dotenv


load_dotenv()

# ↓ 後ほど .env へ格納
DB_PATH = os.path.join(os.path.dirname(__file__), "locations.db")
ELGANA_API_URL = os.getenv("ELGANA_API_URL")
LOGIN_API_URL = os.getenv("LOGIN_API_URL")
ELGANA_UPLOAD_URL = os.getenv("ELGANA_UPLOAD_URL")
RICHMENU_API_URL = os.getenv("RICHMENU_API_URL")
CREATEROOM_API_URL = os.getenv("CREATEROOM_API_URL")
LOGIN_ID = os.getenv("LOGIN_ID")
PASSWORD = os.getenv("PASSWORD")

app = Flask(__name__)


def init_db():
    """
    DB初期化
    locations & potohle テーブルがなければ作成
    """

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS operation_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            msg_id TEXT,
            room_id TEXT,
            user_id TEXT,
            location_id TEXT,
            latitude REAL,
            longitude REAL,
            instruction_id TEXT,
            instruction TEXT,
            status TEXT,
            urgency TEXT,
            customer_info TEXT,
            remarks TEXT,
            received_at TEXT,
            completed TEXT,
            update_at TEXT
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS spot_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            msg_id TEXT,
            image_id TEXT,
            repair_required TEXT,
            hight TEXT,
            width TEXT,
            depth TEXT,
            image_url TEXT,
            image_filename TEXT,
            deleted TEXT 
        )
    """
    )

    conn.commit()
    conn.close()


def get_access_token():
    """
    Elgana にログインしてトークンを取得する

    headers：Elgana へのリクエストヘッダーを定義
    payload：Elgana へのログインIDとパスワードを定義

    response：このリクエストの応答を格納

    response = { result": {"access_token": "#######"}, ..}
    """

    headers = {
        "X-MBL-COMPANY-ID": "infra-sisb",
        "X-MBL-OS": "windows",
        "X-MBL-CLIENT": "10",
        "X-MBL-DID": "123451",
        "Content-Type": "application/json",
    }
    payload = {"login_id": LOGIN_ID, "password": PASSWORD}
    try:
        response = requests.post(LOGIN_API_URL, headers=headers, json=payload)
        print("Login response: ", response.status_code, response.text)
        if response.status_code == 200:
            return response.json().get("result", {}).get("access_token")
        else:
            return None
    except Exception as e:
        print("ログインAPI通信エラー:", e)
        return None


def upload_message(msg_id, tmp_text):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            room_id,
            instruction,
            completed
        FROM operation_orders
        WHERE msg_id = ?
            AND completed IS NOT NULL
    """,
        (msg_id,),
    )
    room_id = cursor.fetchone()
    conn.close()
    message_text = f"""指示: {room_id[1]}
{room_id[2]}
{tmp_text}"""

    upload_message_token = get_access_token()
    message_headers = {
        "X-MBL-COMPANY-ID": "infra-sisb",
        "X-MBL-OS": "windows",
        "X-MBL-CLIENT": "10",
        "X-MBL-DID": "123451",
        "X-MBL-ACCESS-TOKEN": upload_message_token,
        "Content-Type": "application/json",
    }
    message_payload = {
        "extra": "",
        "roomIds": room_id[0],
        "text": message_text,
        "type": "text",
    }
    try:
        message_response = requests.post(
            ELGANA_UPLOAD_URL, headers=message_headers, json=message_payload
        )
        print(
            "upload_message 成功！！:",
            message_response.status_code,
            message_response.text,
        )
    except Exception as ume:
        print("upload_message 失敗！！ :", ume)
        traceback.print_exc()


def download_image(room_id, file_id):
    """
    room_id, file_id を指定した url で subproccess を用いて APIリクエストを行い、
    ・画像のバイナリデータ
    ・保存する際のファイル名                                             を返す
    """

    token = get_access_token()
    if not token:
        print("アクセストークン取得失敗")
        return None, None

    url = f"{ELGANA_API_URL}?roomId={room_id}&fileId={file_id}"
    tmp_path = f"/tmp/{file_id}.jpg"

    try:
        headers = {
            "X-MBL-COMPANY-ID": "infra-sisb",
            "X-MBL-OS": "windows",
            "X-MBL-CLIENT": "10",
            "X-MBL-DID": "123451",
            "X-MBL-ACCESS-TOKEN": token,
            "Content-Type": "application/octet-stream",
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            with open(tmp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        # 取得した jpg ファイルを開き、バイナリデータを image_data に格納
        with open(tmp_path, "rb") as f:
            image_data = f.read()

        # kind.extention で判別したフォーマットの拡張子を返し、filename にfile_id.jpgを格納
        filename = f"{file_id}.jpg"
        return image_data, filename

    except Exception as e:
        print("download image error:", e)
        traceback.print_exc()
        return None, None


def insert_info(
    message_id, room_id, user_id, instruction, status, urgency, customer_info, remarks
):
    """
    ./location.db の operation_orders テーブルにデータを挿入
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO operation_orders (msg_id, room_id, user_id, instruction_id, instruction, status, urgency, customer_info, remarks, received_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                message_id,
                room_id,
                user_id,
                message_id,
                instruction,
                status,
                urgency,
                customer_info,
                remarks,
                now_str,
            ),
        )
        print("insert_info 成功！！")
    except Exception as iie:
        print("insert_info 失敗！！ ", iie)
        traceback.print_exc()
    finally:
        conn.commit()
        conn.close()


def insert_locations(message_id, room_id, user_id, latitude, longitude):
    """
    ./location.db の operation_orders テーブルの該当のカラムに latitude, logitude を追加する
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO operation_orders (msg_id, room_id, user_id, location_id, latitude, longitude, received_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (message_id, room_id, user_id, message_id, latitude, longitude, now_str),
        )
        print("insert_locations 成功！！")
    except Exception as ile:
        print("insert_locations 失敗！！ ", ile)
        traceback.print_exc()
    finally:
        conn.commit()
        conn.close()


def insert_image(message_id, room_id, user_id, filename):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO operation_orders (msg_id, room_id, user_id, received_at)
            VALUES (?, ?, ?, ?)
        """,
            (message_id, room_id, user_id, now_str),
        )
        cursor.execute(
            """
            INSERT INTO spot_info (msg_id, image_id, image_filename, deleted)
            VALUES (?, ?, ?, ?)
        """,
            (message_id, message_id, filename, "0"),
        )
        print("insert_image 成功！！")
    except Exception as iie:
        print("insert_image 失敗！！ ", iie)
        traceback.print_exc()
    finally:
        conn.commit()
        conn.close()


def update_info(
    remessage_id, message_id, instruction, status, urgency, customer_info, remarks
):
    regist = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE operation_orders
            SET
                instruction_id = ?,
                instruction = ?,
                status = ?,
                urgency = ?,
                customer_info = ?,
                remarks = ?,
                update_at = ?
            WHERE
                msg_id = ?
        """,
            (
                message_id,
                instruction,
                status,
                urgency,
                customer_info,
                remarks,
                now_str,
                remessage_id,
            ),
        )
        # cursor.execute("""
        #     SELECT
        #         latitude,
        #         longitude
        #     FROM operation_orders
        #     WHERE msg_id = ?
        # """, (remessage_id,))
        # regist = cursor.fetchone()
        print("update_info 成功！！")
    except Exception as uie:
        print("update_info 失敗！！ ", uie)
        traceback.print_exc()
    finally:
        conn.commit()
        conn.close()
        # if regist[0] is not None and regist[1] is not None:
        #     insert_completed(remessage_id)


def update_locations(remessage_id, message_id, latitude, longitude):
    regist = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE operation_orders
            SET
                location_id = ?,
                latitude = ?,
                longitude = ?,
                update_at = ?
            WHERE
                msg_id = ?
        """,
            (message_id, latitude, longitude, now_str, remessage_id),
        )
        # cursor.execute("""
        #     SELECT
        #         instruction
        #     FROM operation_orders
        #     WHERE msg_id = ?
        # """, (remessage_id,))
        # regist = cursor.fetchone()
        print("update_locations 成功！！")
    except Exception as ule:
        print("update_locations 失敗！！ ", ule)
        traceback.print_exc()
    finally:
        conn.commit()
        conn.close()
        # if regist[0] is not None:
        #     insert_completed(remessage_id)


def update_image(remessage_id, message_id, filename):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO spot_info (msg_id, image_id, image_filename, deleted)
            VALUES (?, ?, ?, ?)
        """,
            (remessage_id, message_id, filename, "0"),
        )
        cursor.execute(
            """
            UPDATE operation_orders
            SET 
                update_at = ?
            WHERE msg_id = ?
        """,
            (now_str, remessage_id),
        )
        print("update_image 成功！！")
    except Exception as uie:
        print("update_image 失敗！！ ", uie)
        traceback.print_exc()
    finally:
        conn.commit()
        conn.close()


def parse_body_text(body_text):
    fields = {
        "①指示": "",
        "②状況": "",
        "③緊急度": "",
        "④お客様情報": "",
        "⑤備考": "",
    }
    for line in body_text.splitlines():
        for key in fields.keys():
            if line.startswith(f"【{key}】"):
                fields[key] = line.replace(f"【{key}】", "").strip()
            elif key == "⑤備考" and line.startswith("【⑤浦考】"):
                fields["⑤備考"] = line.replace("【⑤浦考】", "").strip()
    return fields


@app.route("/elgana_api", methods=["POST"])
def elgana_api():
    data = request.get_json()
    print("Received JSON:", json.dumps(data, indent=2, ensure_ascii=False))

    if (
        not data
        or "msg" not in data
        or "body" not in data["msg"]
        or data["tag"] == "onReadUpdate"
    ):
        return jsonify({"error": "Invalid JSON format"}), 400

    msg = data["msg"]
    body_text = msg["body"]
    room_id = msg["roomId"]
    user_id = msg["userId"]
    message_id = msg["id"]

    print("Raw body_text:\n", body_text)

    if not msg.get("reMsg"):
        if "指示" in body_text and "状況" in body_text and "緊急度" in body_text:
            fields = parse_body_text(body_text)
            instruction = fields["①指示"]
            status = fields["②状況"]
            urgency = fields["③緊急度"]
            customer_info = fields["④お客様情報"]
            remarks = fields["⑤備考"]
            print(f"Parsed fields: {fields}")
            insert_info(
                message_id,
                room_id,
                user_id,
                instruction,
                status,
                urgency,
                customer_info,
                remarks,
            )
            return jsonify({"message": "insert_info successfully"}), 200

        if "位置情報を送信しました" in body_text and msg["extra"]:
            extra_data = json.loads(msg["extra"])
            latitude = extra_data.get("lat")
            longitude = extra_data.get("lon")
            if latitude is not None and longitude is not None:
                insert_locations(message_id, room_id, user_id, latitude, longitude)
                return jsonify({"message": "insert_message successfully"}), 200
            else:
                return jsonify({"error": "Latitude or longitude not found"}), 400

        if msg["type"] == "image":
            file_lines = msg.get("data", "").split("\n")
            print("file_lines:", file_lines)
            for file_id_candidate in file_lines:
                print(f"試行 fileId: {file_id_candidate}")
                image_data, filename = download_image(room_id, file_id_candidate)
                if image_data:
                    print(f"✅ 成功 fileId: {file_id_candidate}")
                    insert_image(message_id, room_id, user_id, filename)
                    return jsonify({"message": "insert_image successfully"}), 200
                else:
                    print("❌ 画像取得に失敗（全fileId試行済）")
                    return jsonify({"error": "Failed to download image"}), 500

        if "テストカルーセル" == body_text:
            carousel_result = upload_carousel(room_id)
            if carousel_result:
                print("upload_carousel success!!")
                return jsonify({"message": "uploadcarousel successfully"}), 200
            else:
                print("upload_carousel failed...")
                return jsonify({"error": "Failed to upload carousel"}), 500

        return jsonify({"error": "Message ignored"}), 400

    elif msg.get("reMsg") and msg.get("reMsg") != "0":
        remessage_id = msg["reMsg"]
        if "指示" in body_text and "状況" in body_text and "緊急度" in body_text:
            fields = parse_body_text(body_text)
            instruction = fields["①指示"]
            status = fields["②状況"]
            urgency = fields["③緊急度"]
            customer_info = fields["④お客様情報"]
            remarks = fields["⑤備考"]
            print(f"Parsed fields: {fields}")
            update_info(
                remessage_id,
                message_id,
                instruction,
                status,
                urgency,
                customer_info,
                remarks,
            )
            return jsonify({"message": "insert_info successfully"}), 200

        if "位置情報を送信しました" in body_text and msg["extra"]:
            extra_data = json.loads(msg["extra"])
            latitude = extra_data.get("lat")
            longitude = extra_data.get("lon")
            if latitude is not None and longitude is not None:
                update_locations(remessage_id, message_id, latitude, longitude)
                return jsonify({"message": "insert_message successfully"}), 200
            else:
                return jsonify({"error": "Latitude or longitude not found"}), 400

        if msg["type"] == "image":
            file_lines = msg.get("data", "").split("\n")
            print("file_lines:", file_lines)
            for file_id_candidate in file_lines:
                print(f"試行 fileId: {file_id_candidate}")
                image_data, filename = download_image(room_id, file_id_candidate)
                if image_data:
                    print(f"✅ 成功 fileId: {file_id_candidate}")
                    update_image(remessage_id, message_id, filename)
                    return jsonify({"message": "insert_image successfully"}), 200
                else:
                    print("❌ 画像取得に失敗（全fileId試行済）")
                    return jsonify({"error": "Failed to download image"}), 500

        return jsonify({"error": "reMessage ignored"}), 400

    return jsonify({"error": "Message ignored"}), 400


class DictCursor(sqlite3.Cursor):
    def fetchall_dict(self):
        return list(map(dict, self.fetchall()))


@app.route("/get_locations", methods=["GET"])
def get_locations():
    locations = []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor(factory=DictCursor)
    cursor.execute(
        """
        SELECT
            msg_id,
            latitude,
            longitude,
            instruction,
            status,
            urgency,
            customer_info,
            remarks,
            completed,
            signal,
            received_at,
            update_at
        FROM operation_orders
    """
    )
    operations = cursor.fetchall_dict()
    for operation in operations:
        signal = operation.get("signal")
        msg_id = operation.get("msg_id")
        if signal == "0":
            continue
        discovery_image_dict_list = []
        before_image_dict_list = []
        after_image_dict_list = []
        cursor.execute(
            """
        SELECT
            s.repair_required,
            s.height,
            s.width,
            s.depth,
            s.image_url,
            s.status_flag,
            s.deleted,
            s.cost,
            s.term,
            u.user_name,
            u.org,
            u.email_address,
            s.create_at
        FROM spot_info AS s
        INNER JOIN user_info AS u ON s.user_id = u.user_id
        WHERE s.msg_id = ?
        """,
            (msg_id,),
        )
        spots = cursor.fetchall_dict()
        if spots:
            for spot in spots:
                repair_required = spot.get("repair_required")
                status_flag = spot.get("status_flag")
                if status_flag == "0":
                    discovery_image_dict_list.append(spot)
                elif status_flag == "1":
                    if repair_required == "true":
                        before_image_dict_list.append(spot)
                    elif repair_required == "false":
                        after_image_dict_list.append(spot)

        if operation["completed"]:
            operation_status = "3"
        elif after_image_dict_list:
            operation_status = "2"
        elif before_image_dict_list:
            operation_status = "1"
        else:
            operation_status = "0"
        operation["operation_status"] = operation_status
        operation["discovery_images"] = discovery_image_dict_list
        operation["before_images"] = before_image_dict_list
        operation["after_images"] = after_image_dict_list
        locations.append(operation)
    conn.close()
    return jsonify(locations)


@app.route("/completed", methods=["POST"])
def completed():

    data = request.get_json()
    msg_id = data.get("msg_id")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not msg_id:
        return ({"error": "msg_id is not correct"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE operation_orders
            SET completed = ?
            WHERE msg_id = ?
        """,
            (now_str, msg_id),
        )
        result_completed_regist = cursor.rowcount
        if result_completed_regist == 1:
            conn.commit()
            result_json = {"message": "completed_regist success!!"}
            result_code = 200
        else:
            conn.rollback()
            result_json = {"message": "completed_regist failed..."}
            result_code = 400
        conn.close()
    except Exception as cre:
        print("completed_regist 失敗！！ ", cre)
        traceback.print_exc()
        result_json = {"error": cre}
        result_code = 400

    if result_code == 200:
        upload_message(msg_id, "作業完了登録をしました。")

    return jsonify(result_json), result_code


@app.route("/deleted", methods=["POST"])
def deleted():
    data = request.get_json()
    msg_id = data.get("msg_id")
    image_url = data.get("image_url")
    deleted = data.get("deleted")

    if msg_id is None or image_url is None or deleted is None:
        return jsonify({"message": "msg_id and image_url are required"}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if deleted == "0":
        try:
            cursor.execute(
                """
                UPDATE spot_info
                SET deleted = "1"
                WHERE msg_id = ?
                    AND image_url = ?
            """,
                (msg_id, image_url),
            )
            result_delete = cursor.rowcount
            if result_delete == 1:
                conn.commit()
                result_json = {"message": "image_delete success!!"}
                result_code = 200
            else:
                conn.rollback()
                result_json = {"message": "image_delete failed..."}
                result_code = 400
            conn.close()
        except Exception as e:
            traceback.print_exc()
            result_json = {"error": "image_deleted error"}
            result_code = 500

    elif deleted == "1":
        try:
            cursor.execute(
                """
                UPDATE spot_info
                SET deleted = "0"
                WHERE msg_id = ?
                    AND image_url = ?
            """,
                (msg_id, image_url),
            )
            result_undeleted = cursor.rowcount
            if result_undeleted == 1:
                conn.commit()
                result_json = {"message": "image_undelete sccess!!"}
                result_code = 200
            else:
                conn.rollback()
                result_json = {"message": "image_delete failed..."}
                result_code = 400
            conn.close()
        except Exception as e:
            traceback.print_exc()
            result_json = {"error": "image_deleted error"}
            result_code = 500

    return jsonify(result_json), result_code


init_db()


if __name__ == "__main__":
    print("Database initialized.")
    app.run(host="0.0.0.0", port=5000, debug=True)
