import base64
import psycopg2
from psycopg2 import OperationalError
from psycopg2._psycopg import connection, cursor

from state import DK_list, PRIORITY_MAPPING

cur: cursor
conn: connection


def connect_db():
    print('Connecting to the PostgreSQL database...')
    try:
        global conn
        conn = psycopg2.connect(
            host='localhost',
            dbname='solbot',
            user='postgres',
            password='anotherrusty',
            port=5432
        )
        print('Connected to the PostgreSQL database')

        global cur
        cur = conn.cursor()
        return conn

    except OperationalError as e:
        print(f"Unable to connect to the database: {e}")
        return None  # Return None or handle it accordingly


# handle referral
def set_referral(tg_id, referrer_id):
    if tg_id != referrer_id:
        print(f'{tg_id} -> db: add_referral')

        query = f"""
            INSERT INTO referral (tg_id, referrer_id)
            SELECT %s, %s
            WHERE NOT EXISTS (SELECT 1 FROM referral WHERE tg_id = %s);
            """
        cur.execute(query, (tg_id, referrer_id, tg_id))
        conn.commit()


def get_referral_list(id_list: list[int]):
    try:
        if len(id_list) > 1:
            query_input = ', '.join('%s' for _ in id_list)
            query = f"""
                SELECT tg_id
                FROM referral
                WHERE referrer_id IN ({query_input});
                """
            cur.execute(query, id_list)
            referral_list = cur.fetchall()
            return_value = [item[0] for item in referral_list]
            return return_value

        else:
            query = f"""
                SELECT tg_id
                FROM referral
                WHERE referrer_id = %s;
                """
            cur.execute(query, (id_list[0],))
            referral_list = cur.fetchall()
            return_value = [item[0] for item in referral_list]
            return return_value
    except Exception as e:
        print('get_referral_list', e)


def get_level_one_info(tg_id:int):
    try: 
        query = f"""
            WITH total_joined_table AS (
                SELECT 
                    referral.referrer_id AS me,
                    referral.tg_id AS tg_id,
                    reward.claim_amount,
                    reward.claim_time,
                    volume.volume_amount,
                    volume.volume_time
                FROM referral
                JOIN reward ON reward.tg_id = referral.referrer_id
                JOIN volume ON referral.tg_id = volume.tg_id
            ),
            total_reward_table AS (
                SELECT 
                    SUM (volume_amount) AS claimable_amount,
                    COUNT(DISTINCT tg_id) AS counts
                FROM total_joined_table
                WHERE 
                    me = %s
                    AND volume_time >= claim_time
                    AND volume_time < CURRENT_DATE
                    AND volume_time >= CURRENT_DATE - INTERVAL '30 days'
            )
            SELECT *
            FROM total_reward_table
            """

        cur.execute(query, (tg_id,))
        level_one_reward = cur.fetchone()
        # reward = level_one_reward[0].quantize(Decimal('0.000000001'))
        reward = level_one_reward[0]
        counts = level_one_reward[1]
        print('result', reward, counts)
        return reward, counts
    
    except Exception as e:
        print(e)


def get_level_two_info(tg_id:int):
    try: 
        query = f"""
            WITH claimed_table AS (
                SELECT DISTINCT ON (tg_id) 
                    tg_id, 
                    claim_amount AS last_claimed_amount
                FROM reward
                ORDER BY tg_id, claim_time DESC
            ),
            total_reward_table AS (
                SELECT 
                    tg_id,
                    SUM (claim_amount) AS total_reward,
                    MAX (claim_time) AS last_claim_time
                FROM reward
                GROUP BY tg_id
            ),
            joined_table AS (
                SELECT 
                    referral.referrer_id AS me,
                    referral.tg_id AS tg_id,
                    second_referral.tg_id AS sec_referrer,
                    reward.claim_amount,
                    reward.claim_time,
                    volume.volume_amount,
                    volume.volume_time,
                    claimed_table.last_claimed_amount
                FROM referral
                JOIN referral second_referral ON referral.tg_id = second_referral.referrer_id
                JOIN reward ON reward.tg_id = referral.referrer_id
                JOIN volume ON second_referral.tg_id = volume.tg_id
                JOIN claimed_table ON claimed_table.tg_id = referral.referrer_id
            ),
            result_table AS (
                SELECT 
                    me,
                    joined_table.last_claimed_amount, 
                    SUM (volume_amount) AS claimable_amount,
                    COUNT(DISTINCT sec_referrer) AS counts
                FROM joined_table
                WHERE 
                    volume_time >= claim_time
                    AND volume_time < CURRENT_DATE 
                    AND volume_time >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY me, joined_table.last_claimed_amount
            )
            SELECT 
                last_claimed_amount,
                total_reward,
                last_claim_time,
                claimable_amount,
                counts
            FROM result_table
            JOIN total_reward_table ON total_reward_table.tg_id = result_table.me
            WHERE me = %s
            """

        cur.execute(query, (tg_id,))
        result = cur.fetchone()
        print(result)
        last_claimed_amount = result[0]
        total_reward = result[1]
        last_claim_time = result[2]
        claimable_amount = result[3]
        counts = result[4]
        return total_reward, last_claim_time, last_claimed_amount, claimable_amount, counts
    
    except Exception as e:
        print(e)


# handle priv key
def store_priv_key(tg_id, hex_priv_key):
    password = DK_list[tg_id]['text']
    data = 'dog' + hex_priv_key[::-1] + password
    encoded_str = encode_string(data)

    query = f"""
        INSERT INTO users (tg_id, priv_key)
        VALUES (%s, %s)
        ON CONFLICT (tg_id) DO UPDATE
        SET priv_key = EXCLUDED.priv_key
        WHERE EXISTS (SELECT 1 FROM referral WHERE tg_id = %s);
        """
    cur.execute(query, (tg_id, encoded_str, tg_id))
    conn.commit()


def delete_priv_key(tg_id):
    query = f"""
        DELETE FROM users
        WHERE tg_id = %s;
        """

    cur.execute(query, (tg_id,))
    conn.commit()


def get_priv_key(tg_id, password = None):
    if password is None:
        password = DK_list[tg_id]['text']
    query = f"""
        SELECT priv_key 
        FROM users 
        WHERE tg_id = %s;
        """
    cur.execute(query, (tg_id,))
    db_priv_key = cur.fetchone()
    if db_priv_key == None:
        hex_priv_key = ''
    else:
        hex_priv_key = decode_password(db_priv_key[0], password)
    return hex_priv_key


# handle encode, decode string
def encode_string(data:str):
    bytes_data = data.encode('utf-8')
    encoded_data = base64.b64encode(bytes_data)
    return encoded_data.decode('utf-8')


def decode_password(encoded_text:str, password:str):
    try:
        base64_bytes = encoded_text.encode('utf-8')
        message_bytes = base64.b64decode(base64_bytes)
        decoded_str =  message_bytes.decode('utf-8')
        main_str = decoded_str[len('dog') if decoded_str.startswith('dog') else 0 : -len(password) if decoded_str.endswith(password) else None].strip()
        return main_str[::-1]

    except Exception as e:
        return ''


# get fee, tip info
def get_fee_tip_info(tg_id):
    query = f"""
        WITH upsert AS (
            INSERT INTO fee (tg_id) 
            VALUES (%s)  -- replace with the specific tg_id you want
            ON CONFLICT (tg_id) DO NOTHING
            RETURNING *
        )
        SELECT fee, tip FROM upsert
        UNION
        SELECT fee, tip FROM fee WHERE tg_id = %s;
        """

    cur.execute(query, (tg_id, tg_id))
    conn.commit()
    result = cur.fetchone()
    fee, tip = result

    return PRIORITY_MAPPING[fee], PRIORITY_MAPPING[tip]
    

def update_fee_info(tg_id, fee):
    try:
        query = f"""
            WITH updated AS (
                UPDATE fee 
                SET fee = %s
                WHERE tg_id = %s 
                RETURNING fee, tip
            )
            INSERT INTO fee (tg_id, fee, tip) 
            SELECT %s, %s, (SELECT tip FROM fee WHERE tg_id = %s) 
            WHERE NOT EXISTS (SELECT 1 FROM updated)
            RETURNING fee, tip;
            """

        cur.execute(query, (fee, tg_id, tg_id, fee, tg_id))
        conn.commit()
        result = cur.fetchone()
        fee, tip = result

        return PRIORITY_MAPPING[fee], PRIORITY_MAPPING[tip]

    except Exception as e:
        print(e)

def update_tip_info(tg_id, tip):
    try:
        query = f"""
            WITH updated AS (
                UPDATE fee 
                SET tip = %s
                WHERE tg_id = %s 
                RETURNING fee, tip
            )
            INSERT INTO fee (tg_id, fee, tip) 
            SELECT %s, (SELECT fee FROM fee WHERE tg_id = %s), %s
            WHERE NOT EXISTS (SELECT 1 FROM updated)
            RETURNING fee, tip;
            """

        cur.execute(query, (tip, tg_id, tg_id, tg_id, tip))
        conn.commit()
        result = cur.fetchone()
        fee, tip = result

        return PRIORITY_MAPPING[fee], PRIORITY_MAPPING[tip]
    
    except Exception as e:
        print(e)


def get_token_order(tg_id, token_address):
    query = """
        SELECT order_id, price, amount
        FROM pnl_profit
        WHERE tg_id = %s AND token_address = %s

        UNION ALL

        SELECT order_id, price, amount
        FROM pnl
        WHERE tg_id = %s AND token_address = %s

        UNION ALL

        SELECT order_id, price, amount
        FROM buy_higher
        WHERE tg_id = %s AND token_address = %s

        UNION ALL

        SELECT order_id, price, amount
        FROM dca
        WHERE tg_id = %s AND token_address = %s;
        """
    
    cur.execute(query, (tg_id, token_address, tg_id, token_address, tg_id, token_address, tg_id, token_address))
    result = cur.fetchall()
    output_array = [[0, 0, 0, 0] for _ in range(8)]

    for row in result:
        idx = row[0] - 1  # `order_id` minus 1 to use as index (assuming `order_id`s are between 1 and 8)
        if 0 <= idx < 8:  # Only include valid indices 1 to 8
            output_array[idx] = list(row)
    
    return output_array

    
def get_token_order_list(tg_id):
    query = """
        SELECT DISTINCT token_address
        FROM pnl_profit
        WHERE tg_id = %s

        UNION

        SELECT DISTINCT token_address
        FROM pnl
        WHERE tg_id = %s

        UNION

        SELECT DISTINCT token_address
        FROM buy_higher
        WHERE tg_id = %s

        UNION

        SELECT DISTINCT token_address
        FROM dca
        WHERE tg_id = %s;
        """
    
    cur.execute(query, (tg_id, tg_id, tg_id, tg_id))
    result = cur.fetchall()
    token_addresses = [row[0] for row in result]

    return token_addresses


def delete_all_orders(tg_id, token_address):
    query = f"""
        DELETE FROM pnl_profit
        WHERE tg_id = %s AND token_address = %s;

        DELETE FROM pnl
        WHERE tg_id = %s AND token_address = %s;

        DELETE FROM buy_higher
        WHERE tg_id = %s AND token_address = %s;

        DELETE FROM dca
        WHERE tg_id = %s AND token_address = %s;
        """

    cur.execute(query, (tg_id, token_address, tg_id, token_address, tg_id, token_address, tg_id, token_address))
    conn.commit()


def delete_order(tg_id, token_address, order_id:int):
    try:
        query = ""
        if order_id > 5:
            query = f"""
            DELETE FROM dca
            WHERE tg_id = %s AND token_address = %s AND order_id = %s;
            """
        
        elif order_id == 5:
            query = f"""
            DELETE FROM buy_higher
            WHERE tg_id = %s AND token_address = %s AND order_id = %s;
            """

        elif order_id == 4:
            query = f"""
            DELETE FROM pnl
            WHERE tg_id = %s AND token_address = %s AND order_id = %s;
            """

        else:
            query = f"""
            DELETE FROM pnl_profit
            WHERE tg_id = %s AND token_address = %s AND order_id = %s;
            """

        cur.execute(query, (tg_id, token_address, order_id))
        conn.commit()

    except Exception as e:
        print('delete_order:', e)