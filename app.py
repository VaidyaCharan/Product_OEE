from flask import Flask, render_template, jsonify, send_file
import pyodbc, threading, time, logPLC, random
import pandas as pd

from io import BytesIO
from waitress import serve
from logPLC import get_machine_data

app = Flask(__name__)

# Database connection string
conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=Subros_OEE;"
    "Trusted_Connection=yes;"
)

# Organization Details & Other Dynmic Parameter Configuration (No Of Machine, Org Name)
org = "Subros"
max_machine = 3
DesignedBy = "Control Via Technologies - Smart Control for Smart Manufacturig"
t = random.uniform(0, 100)

# ========== Start logPLC in background ==========
def run_log_plc():
    logPLC.main()
threading.Thread(target=run_log_plc, daemon=True).start()

# ========== DB Connection ==========
def get_db_connection():
    return pyodbc.connect(conn_str)

def insert_machine_data(machine_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("EXEC InsertMachineData ?", machine_id)
        conn.commit()
    except Exception as e:
        print(f"[X] Error Machine {machine_id}: {e}")
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception as close_error:
            print(f"[!] Error closing connection: {close_error}")

def periodic_loop():
    while True:
        for machine_id in range(1, max_machine):
            insert_machine_data(machine_id)
        time.sleep(5)  # delay
threading.Thread(target=periodic_loop, daemon=True).start()

# ========== Routes ==========
@app.route('/')
def navigation():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Machine_Name, OEE, AVA, PFR, QUA FROM MachineDetails")
    rows = cursor.fetchall()
    conn.close()

    m_name = [r.Machine_Name for r in rows]
    data_OEE = [r.OEE for r in rows]
    data_AVA = [r.AVA for r in rows]
    data_PFR = [r.PFR for r in rows]
    data_QUA = [r.QUA for r in rows]

    return render_template(
        'navigation.html',
        m_name=m_name,
        data_OEE=data_OEE,
        data_AVA=data_AVA,
        data_PFR=data_PFR,
        data_QUA=data_QUA,
        org = org,
        max_machine = max_machine, DesignedBy=DesignedBy
    )

@app.route('/dashboard/<int:machine_id>')
def machine_dashboard(machine_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT TOP 1 AVA, PFR, QUA, OEE, Machine_Name
        FROM MachineDetails
        WHERE Machine_ID = ?
        ORDER BY Machine_ID DESC
    """
    cursor.execute(query, machine_id)
    row = cursor.fetchone()
    conn.close()

    # Oee_Matrix = get_machine_data(machine_id)

    data = {
        'machine_name': row.Machine_Name if row else 'N/A',
        'availability': row.AVA if row else 0,
        'performance': row.PFR if row else 0,
        'quality': row.QUA if row else 0,
        'oee': row.OEE if row else 0
    }
    return render_template('dashboard.html', machine_id=machine_id, data=data, org = org,
        max_machine = max_machine, DesignedBy=DesignedBy)

@app.route('/settings/<int:machine_id>/<machine_name>')
def settings(machine_id, machine_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = f"SELECT * FROM MC_{machine_id} ORDER BY ID DESC"
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return render_template('settings.html', data=rows, machine_id=machine_id, machine_name=machine_name, org = org,
        max_machine = max_machine, DesignedBy=DesignedBy)

@app.route('/api/machine_data')
def machine_data():
    result = []

    for i in range(1, max_machine):  # +1 to include max_machine in the range
        try:
            data = get_machine_data(i)
            availability = round(data['AVA'], 2)
            performance = round(data['PFR'], 2)
            quality = round(data['QUA'], 2)
            oee = (availability * performance * quality) / 10000

            result.append({
                "id": i,
                "availability": availability,
                "performance": performance,
                "quality": quality,
                "oee": round(oee, 3)
            })
        except Exception as e:
            print(f"[!] Error fetching data for machine {i}: {e}")
            result.append({
                "id": i,
                "availability": 0,
                "performance": 0,
                "quality": 0,
                "oee": 0
            })

    return jsonify(result)

@app.route('/get_settings_data/<int:machine_id>')
def get_settings_data(machine_id):
    table_name = f"MC_{machine_id}"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name} ORDER BY ID DESC")
    rows = cursor.fetchall()
    conn.close()

    # Convert rows to list of dictionaries
    columns = [col[0] for col in cursor.description]
    data = [dict(zip(columns, row)) for row in rows]
    return jsonify(data)

@app.route('/api/oee/<int:machine_id>')
def get_oee_data(machine_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT TOP 1 AVA, PFR, QUA, OEE
        FROM MachineDetails
        WHERE Machine_ID = ?
        ORDER BY Machine_ID DESC
    """
    cursor.execute(query, machine_id)
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({
            "availability": float(row.AVA),
            "performance": float(row.PFR),
            "quality": float(row.QUA),
            "oee": (float(row.AVA) * float(row.PFR) * float(row.QUA)) /10000
        })
    else:
        return jsonify({
            "availability": 0,
            "performance": 0,
            "quality": 0,
            "oee": 0
        })

@app.route('/api/production_data/<int:machine_id>') 
def get_production_data(machine_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = f"SELECT PlanQtyShft, ActualShift FROM MC_{machine_id} ORDER BY T_Timestamp DESC"
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    return jsonify([
        {"plan": row.PlanQtyShft, "actual": row.ActualShift} for row in rows
    ])

@app.route('/export/excel/<int:machine_id>')
def export_excel(machine_id):
    conn = None
    try:
        conn = get_db_connection()
        query = f"SELECT * FROM MC_{machine_id} ORDER BY ID DESC"
        df = pd.read_sql(query, conn)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=f'MC_{machine_id}_Data')

        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name=f'MC_{machine_id}_Export_{t}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        return jsonify({"error": f"Failed to export data: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ========== Run Server ==========
if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)
