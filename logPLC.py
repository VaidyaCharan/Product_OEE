import snap7, time, random, pyodbc

from snap7.util import get_real
from datetime import datetime


# SQL Server Configuration
DB_CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=Subros_OEE;"
    "Trusted_Connection=yes;"
)

# Define PLCs and connected machines
PLCs = [
    {"ip": "192.168.0.101", "rack": 0, "slot": 1, "machine_ids": [1]},
    {"ip": "192.168.0.102", "rack": 0, "slot": 1, "machine_ids": [2]},    
]

DB_NUMBER = 1000
BYTES_PER_MACHINE = 16  # 4 REALs x 4 bytes


def connect_to_plc(ip, rack, slot):
    client = snap7.client.Client()
    client.connect(ip, rack, slot)
    if not client.get_connected():
        raise ConnectionError(f"Connection failed for PLC {ip}")
    return client


def read_oee_for_machine(client, machine_index):
    offset = BYTES_PER_MACHINE * machine_index
    data = client.db_read(DB_NUMBER, offset, BYTES_PER_MACHINE)

    ava = round(get_real(data, 0),2)
    pfr = round(get_real(data, 4),2)
    qua = round(get_real(data, 8),2)
    oee = round((ava * pfr * qua) / 10000,2)
    return ava, pfr, qua, oee

def update_machine_in_db(machine_id, ava, pfr, qua, oee,):
    conn = pyodbc.connect(DB_CONNECTION_STRING)
    cursor = conn.cursor()


    # Random value move 
    planqty = round(random.uniform(0, 100), 2)


    query = """
        UPDATE MachineDetails
        SET AVA = ?, PFR = ?, QUA = ?, OEE = ?, PlanQtyShft = ?, ActualShift = ?
        WHERE Machine_ID = ?
    """
    cursor.execute(query, (ava, pfr, qua, oee, 200.0, planqty, machine_id))
    conn.commit()
    cursor.close()
    conn.close()


def process_plc(plc_config):
    try:
        client = connect_to_plc(plc_config["ip"], plc_config["rack"], plc_config["slot"])
        print(f"[{datetime.now()}] Connected to PLC: {plc_config['ip']}")

        for idx, machine_id in enumerate(plc_config["machine_ids"]):
            try:
                ava, pfr, qua, oee = read_oee_for_machine(client, idx)
                update_machine_in_db(machine_id, ava, pfr, qua, oee)
                print(f"[{datetime.now()}] PLC {plc_config['ip']} - Machine {machine_id} -> AVA: {ava:.2f}, PFR: {pfr:.2f}, QUA: {qua:.2f}, OEE: {oee:.2f}")
            except Exception as e:
                print(f"[{datetime.now()}] Error reading/writing for Machine {machine_id}: {e}")

        client.disconnect()
        print(f"[{datetime.now()}] Disconnected from PLC: {plc_config['ip']}")

    except Exception as e:
        print(f"[{datetime.now()}] Failed to process PLC {plc_config['ip']}: {e}")

def get_plc_config_for_machine(machine_id):
    for plc in PLCs:
        if machine_id in plc["machine_ids"]:
            index = plc["machine_ids"].index(machine_id)
            return plc, index
    raise ValueError(f"Machine ID {machine_id} not found in any PLC configuration.")

def get_machine_data(machine_id):
    plc_config, index = get_plc_config_for_machine(machine_id)
    client = connect_to_plc(plc_config["ip"], plc_config["rack"], plc_config["slot"])

    offset = BYTES_PER_MACHINE * index
    data = client.db_read(DB_NUMBER, offset, BYTES_PER_MACHINE)

    ava = get_real(data, 0)
    pfr = get_real(data, 4)
    qua = get_real(data, 8)
    oee = (ava * pfr * qua) / 10000
    
    client.disconnect()
    return {"AVA": ava, "PFR": pfr, "QUA": qua, "OEE": oee}

def main():
    while True:
        for plc in PLCs:
            process_plc(plc)
        time.sleep(1)  # Update interval

if __name__ == "__main__":
    main()
