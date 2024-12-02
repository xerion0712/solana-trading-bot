import base64
import logging
import os

from dotenv import find_dotenv, load_dotenv
from psycopg_pool import ConnectionPool
from solbot.state import PRIORITY_MAPPING, DK_list
from solbot.web3.basic import get_token_information

load_dotenv(find_dotenv())

logger = logging.getLogger("solbot")


class Database:
    def __init__(self) -> None:
        self.pool = None
        try:
            self.pool = ConnectionPool(
                conninfo=os.environ["DATABASE_URI"],
                check=ConnectionPool.check_connection,
            )
            self.pool.wait()
            logger.info("database connected")
        except Exception:
            logger.exception("Unable to connect to the database")

    def close(self) -> None:
        if self.pool:
            self.pool.close()


db: Database | None = None


def connect_db():
    """establish database connection"""
    global db

    if not db:
        db = Database()
    else:
        logger.warning('Database connection already exists')


def set_referral(tg_id, referrer_id):
    """handle referral"""
    if tg_id != referrer_id:
        logger.info(f'{tg_id} -> db: add_referral')

        query = """
            INSERT INTO referral (tg_id, referrer_id)
            SELECT %s, %s
            WHERE NOT EXISTS (SELECT 1 FROM referral WHERE tg_id = %s);
            """
        with db.pool.connection() as conn:
            conn.execute(query, (tg_id, referrer_id, tg_id))


def get_referral_list(id_list: list[int]):
    try:
        if len(id_list) > 1:
            query_input = ', '.join('%s' for _ in id_list)
            query = f"""
                SELECT tg_id
                FROM referral
                WHERE referrer_id IN ({query_input});
                """
            with db.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, id_list)
                    referral_list = cur.fetchall()
                    return_value = [item[0] for item in referral_list]
                    return return_value

        else:
            query = """
                SELECT tg_id
                FROM referral
                WHERE referrer_id = %s;
                """
            with db.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (id_list[0],))
                    referral_list = cur.fetchall()
                    return_value = [item[0] for item in referral_list]
                    return return_value
    except Exception:
        logger.exception("Failed to get referral list")


def get_level_one_info(tg_id:int):
    try:
        query = """
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
        with db.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (tg_id,))
                level_one_reward = cur.fetchone()
                reward = level_one_reward[0] if level_one_reward[0] else 0
                counts = level_one_reward[1]
                return reward, counts

    except Exception:
        logger.exception("Failed to get referral list")


def get_level_two_info(tg_id:int):
    try:
        query = """
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
        with db.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (tg_id,))
                result = cur.fetchone()
        last_claimed_amount = result[0] if result and result[0] else 0
        total_reward = result[1] if result and result[1] else 0
        last_claim_time = result[2] if result and result[2] else 0
        claimable_amount = result[3] if result and result[3] else 0
        counts = result[4] if result and result[4] else 0
        return total_reward, last_claim_time, last_claimed_amount, claimable_amount, counts

    except Exception:
        logger.exception("Failed to get level two info")


def encode_string(data:str) -> str:
    bytes_data = data.encode('utf-8')
    encoded_data = base64.b64encode(bytes_data)
    return encoded_data.decode('utf-8')


def decode_password(encoded_text:str, password:str) -> str:
    try:
        base64_bytes = encoded_text.encode('utf-8')
        message_bytes = base64.b64decode(base64_bytes)
        decoded_str =  message_bytes.decode('utf-8')
        main_str = decoded_str[len('dog') if decoded_str.startswith('dog') else 0 : -len(password) if decoded_str.endswith(password) else None].strip()
        return main_str[::-1]

    except Exception as e:
        logger.exception("Failed to decode password")
        return ''


def get_fee_tip_info(tg_id):
    query = """
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
    with db.pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (tg_id, tg_id))
            conn.commit()
            result = cur.fetchone()
            fee, tip = result

    return PRIORITY_MAPPING[fee], PRIORITY_MAPPING[tip]


def update_fee_info(tg_id, fee):
    try:
        query = """
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
        with db.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (fee, tg_id, tg_id, fee, tg_id))
                conn.commit()
                result = cur.fetchone()
                fee, tip = result

        return PRIORITY_MAPPING[fee], PRIORITY_MAPPING[tip]

    except Exception:
        logger.exception("Failed to update fee info")


def update_tip_info(tg_id, tip):
    try:
        query = """
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
        with db.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (tip, tg_id, tg_id, tg_id, tip))
                conn.commit()
                result = cur.fetchone()
                fee, tip = result

        return PRIORITY_MAPPING[fee], PRIORITY_MAPPING[tip]

    except Exception:
        logger.exception("Failed to update tip info")


def store_trading_volume_info(tg_id, amount):
    query = """
    INSERT INTO volume (tg_id, volume_time, volume_amount)
    VALUES (%s, CURRENT_DATE, %s)
    """
    with db.pool.connection() as conn:
        conn.execute(query, (tg_id, amount))


def get_token_order(tg_id, token_address):
    query = """
        SELECT order_id, price, amount
        FROM sell_for_profit
        WHERE tg_id = %s AND token_address = %s

        UNION ALL

        SELECT order_id, price, amount
        FROM sell_for_loss
        WHERE tg_id = %s AND token_address = %s

        UNION ALL

        SELECT order_id, price, amount
        FROM buy_higher
        WHERE tg_id = %s AND token_address = %s

        UNION ALL

        SELECT order_id, price, amount
        FROM buy_lower
        WHERE tg_id = %s AND token_address = %s;
        """

    with db.pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (tg_id, token_address, tg_id, token_address, tg_id, token_address, tg_id, token_address))
            result = cur.fetchall()

    output_array = [[0, 0, 0, 0] for _ in range(8)]
    for row in result:
        idx = row[0] - 1
        if 0 <= idx < 8:
            output_array[idx] = list(row)

    return output_array


def get_token_order_list(tg_id):
    query = """
        SELECT DISTINCT token_address
        FROM sell_for_profit
        WHERE tg_id = %s

        UNION

        SELECT DISTINCT token_address
        FROM sell_for_loss
        WHERE tg_id = %s

        UNION

        SELECT DISTINCT token_address
        FROM buy_higher
        WHERE tg_id = %s

        UNION

        SELECT DISTINCT token_address
        FROM buy_lower
        WHERE tg_id = %s;
        """

    with db.pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (tg_id, tg_id, tg_id, tg_id))
            result = cur.fetchall()

    token_addresses = [row[0] for row in result]
    return sorted(token_addresses)


def get_order(tg_id, token, order_id):
    query = ''

    if order_id < 4:
        query = """
            SELECT *
            FROM sell_for_profit
            WHERE tg_id = %s AND token_address = %s AND order_id = %s;
            """

    elif order_id == 4:
        query = """
            SELECT *
            FROM sell_for_loss
            WHERE tg_id = %s AND token_address = %s AND order_id = %s;
            """

    elif order_id == 5:
        query = """
            SELECT *
            FROM buy_higher
            WHERE tg_id = %s AND token_address = %s AND order_id = %s;
            """

    else:
        query = """
            SELECT *
            FROM buy_lower
            WHERE tg_id = %s AND token_address = %s AND order_id = %s;
            """

    with db.pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (tg_id, token, order_id))
            row = cur.fetchone()

    if row:
        _, _, _, _, price, amount = row
        return price, amount
    else:
        return 0, 0


def delete_all_orders(tg_id, token_address):
    query = """
        DELETE FROM sell_for_profit
        WHERE tg_id = %s AND token_address = %s;

        DELETE FROM sell_for_loss
        WHERE tg_id = %s AND token_address = %s;

        DELETE FROM buy_higher
        WHERE tg_id = %s AND token_address = %s;

        DELETE FROM buy_lower
        WHERE tg_id = %s AND token_address = %s;
        """

    with db.pool.connection() as conn:
        conn.execute(query, (tg_id, token_address, tg_id, token_address, tg_id, token_address, tg_id, token_address))


def delete_order(tg_id, token_address, order_id:int):
    try:
        query = ""
        if order_id > 5:
            query = """
            DELETE FROM buy_lower
            WHERE tg_id = %s AND token_address = %s AND order_id = %s;
            """

        elif order_id == 5:
            query = """
            DELETE FROM buy_higher
            WHERE tg_id = %s AND token_address = %s AND order_id = %s;
            """

        elif order_id == 4:
            query = """
            DELETE FROM sell_for_loss
            WHERE tg_id = %s AND token_address = %s AND order_id = %s;
            """

        else:
            query = """
            DELETE FROM sell_for_profit
            WHERE tg_id = %s AND token_address = %s AND order_id = %s;
            """

        with db.pool.connection() as conn:
            conn.execute(query, (tg_id, token_address, order_id))

    except Exception:
        logger.exception("Failed delete order")


def sell_for_profit_order_update(tg_id, token_address, order_id, price, amount):
    update_query = """
        UPDATE sell_for_profit
        SET price = %s, amount = %s
        WHERE tg_id = %s AND token_address = %s AND order_id = %s;
    """

    with db.pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(update_query, (price, amount, tg_id, token_address, order_id))

            if cur.rowcount == 0:
                insert_query = """
                    INSERT INTO sell_for_profit (tg_id, token_address, order_id, price, amount)
                    VALUES (%s, %s, %s, %s, %s)
                """

                cur.execute(insert_query, (tg_id, token_address, order_id, price, amount))


def sell_for_loss_order_update(tg_id, token_address, order_id, price, amount):
    update_query = """
        UPDATE sell_for_loss
        SET price = %s, amount = %s
        WHERE tg_id = %s AND token_address = %s AND order_id = %s;
    """

    with db.pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(update_query, (price, amount, tg_id, token_address, order_id))

            if cur.rowcount == 0:
                insert_query = """
                    INSERT INTO sell_for_loss (tg_id, token_address, order_id, price, amount)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cur.execute(insert_query, (tg_id, token_address, order_id, price, amount))


def buy_higher_order_update(tg_id, token_address, order_id, price, amount):
    update_query = """
        UPDATE buy_higher
        SET price = %s, amount = %s
        WHERE tg_id = %s AND token_address = %s AND order_id = %s;
    """
    logger.info(f"tg_id:{tg_id}, token_address:{token_address}, order_id:{order_id}, price:{price}, amount:{amount}")

    with db.pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(update_query, (price, amount, tg_id, token_address, order_id))

            if cur.rowcount == 0:
                insert_query = """
                    INSERT INTO buy_higher (tg_id, token_address, order_id, price, amount)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cur.execute(insert_query, (tg_id, token_address, order_id, price, amount))


def buy_lower_order_update(tg_id, token_address, order_id, price, amount):
    update_query = """
        UPDATE buy_lower
        SET price = %s, amount = %s
        WHERE tg_id = %s AND token_address = %s AND order_id = %s;
    """
    logger.info(f"tg_id:{tg_id}, token_address:{token_address}, order_id:{order_id}, price:{price}, amount:{amount}")
    with db.pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(update_query, (price, amount, tg_id, token_address, order_id))

            if cur.rowcount == 0:
                insert_query = """
                    INSERT INTO buy_lower (tg_id, token_address, order_id, price, amount)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cur.execute(insert_query, (tg_id, token_address, order_id, price, amount))


def add_hot_token(tg_id, token):
    # query = f"""
    #     INSERT INTO hot_token (tg_id, token)
    #     VALUES (%s, %s)
    #     ON CONFLICT (tg_id) DO NOTHING
    # """

    with db.pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("BEGIN;")
            cur.execute("DELETE FROM hot_token WHERE tg_id = %s;", (tg_id,))
            cur.execute("INSERT INTO hot_token (tg_id, token) VALUES (%s, %s);", (tg_id, token))
            conn.commit()

            return False if cur.rowcount == 0 else True


def remove_hot_token(tg_id, token):
    query = """
        DELETE FROM hot_token
        WHERE tg_id = %s AND token = %s;
    """

    with db.pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (tg_id, token))
            conn.commit()

            return False if cur.rowcount == 0 else True


def check_hot_token(tg_id, token):
    query = """
        SELECT COUNT(*)
        FROM hot_token
        WHERE tg_id = %s AND token = %s
    """

    with db.pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (tg_id, token))
            row = cur.fetchone()

            if row is None:
                return False

            count = row[0]

            return True if count > 0 else False


def check_preset(tg_id):
    select_query = """
        WITH upsert AS (
            INSERT INTO strategy (tg_id)
            VALUES (%s)
            ON CONFLICT (tg_id) DO NOTHING
            RETURNING *
        )
        SELECT * FROM upsert
        UNION
        SELECT * FROM strategy WHERE tg_id = %s;
    """

    with db.pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(select_query, (tg_id, tg_id))
            row = cur.fetchone()
            return row


def update_preset(tg_id, price0, amount0, price1, amount1, price2, amount2, price3, amount3):
    try:
        query = """
            UPDATE strategy
            SET
                price0 = %s,
                amount0 = %s,
                price1 = %s,
                amount1 = %s,
                price2 = %s,
                amount2 = %s,
                price3 = %s,
                amount3 = %s
            WHERE tg_id = %s
            RETURNING *;
            """
        with db.pool.connection() as conn:
            conn.execute(query, (price0, amount0, price1, amount1, price2, amount2, price3, amount3, tg_id))

    except Exception:
        logger.exception("Failed to update_preset")


def apply_preset(tg_id, token):
    try:
        token_price = get_token_information(token)[3]

        select_query = """
            SELECT * FROM strategy
            WHERE tg_id = %s;
        """

        with db.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(select_query, (tg_id, ))
                row = cur.fetchone()

                if row is None:
                    select_query = """
                        WITH upsert AS (
                            INSERT INTO strategy (tg_id)
                            VALUES (%s)
                            ON CONFLICT (tg_id) DO NOTHING
                            RETURNING *
                        )
                        SELECT * FROM upsert
                        UNION
                        SELECT * FROM strategy WHERE tg_id = %s;
                    """

                    cur.execute(select_query, (tg_id, tg_id))

                cur.execute(select_query, (tg_id, ))
                row = cur.fetchone()

        _, _, percentage1, amount1, percentage2, amount2, percentage3, amount3, percentage4, amount4 = row
        price1 = float(token_price) * (float(percentage1) + 100) / 100
        price2 = float(token_price) * (float(percentage2) + 100) / 100
        price3 = float(token_price) * (float(percentage3) + 100) / 100
        price4 = float(token_price) * (100 - float(percentage4)) / 100

        update_as_preset_sell_for_profit(tg_id, token, 1, price1, amount1)
        update_as_preset_sell_for_profit(tg_id, token, 2, price2, amount2)
        update_as_preset_sell_for_profit(tg_id, token, 3, price3, amount3)
        update_as_preset_sell_for_loss(tg_id, token, 4, price4, amount4)

        return price1, amount1, price2, amount2, price3, amount3, price4, amount4

    except Exception:
        logger.exception("Failed to apply preset")


def update_as_preset_sell_for_profit(tg_id, token_address, order_id, price, amount):
    try:
        query = """
            INSERT INTO sell_for_profit (tg_id, token_address, order_id, price, amount)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (tg_id, token_address, order_id)
            DO UPDATE SET price = EXCLUDED.price, amount = EXCLUDED.amount
            RETURNING *;
            """

        with db.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (tg_id, token_address, order_id, price, amount))
                conn.commit()

                return cur.fetchone()

    except Exception:
        logger.exception('Failed to update_as_preset_profit')


def update_as_preset_sell_for_loss(tg_id, token_address, order_id, price, amount):
    try:
        query = """
            INSERT INTO sell_for_loss (tg_id, token_address, order_id, price, amount)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (tg_id, token_address, order_id)
            DO UPDATE SET price = EXCLUDED.price, amount = EXCLUDED.amount
            RETURNING *;
            """

        with db.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (tg_id, token_address, order_id, price, amount))
                conn.commit()

                return cur.fetchone()

    except Exception:
        logger.exception('Failed to update_as_preset_loss')


def add_watch_list(tg_id, token):
    query = """
        INSERT INTO watch_list (tg_id, token_addr)
        VALUES (%s, %s)
        ON CONFLICT(tg_id, token_addr) DO NOTHING;
        """

    with db.pool.connection() as conn:
        conn.execute(query, (tg_id, token))


def remove_watch_list(tg_id, token):
    query = """
        DELETE FROM watch_list
        WHERE tg_id = %s AND token_addr = %s;
        """

    with db.pool.connection() as conn:
        conn.execute(query, (tg_id, token))


def get_watch_list(tg_id):
    query = """
        SELECT ARRAY_AGG(token_addr)
        FROM watch_list
        WHERE tg_id = %s;
        """

    with db.pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (tg_id,))
            row = cur.fetchone()[0]
            return row
