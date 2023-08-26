import socket
import threading
import time
import keyboard

message_list = []
input_str = ""
last_snapshot = ""
refresh_needed = True


def add_local_message(msg):
    global refresh_needed
    message_list.append(str(msg))
    refresh_needed = True


def draw_window(title):
    global last_snapshot, refresh_needed
    while True:
        if refresh_needed:
            print("\033c", end="")  # Clear terminal (may not work on all platforms)
            print(title)
            print("-" * 40)

            for message in message_list[-10:]:  # Display only the last 10 messages
                print(message)

            print("-" * 40)
            print(f"> {input_str}", end="", flush=True)

            last_snapshot = "\n".join(message_list[-10:]) + input_str
            refresh_needed = False
        time.sleep(0.01)


def on_key_send(event, other):
    global input_str, refresh_needed
    if event.name == 'enter':
        message_list.append("< " + input_str)
        other.send(input_str.encode("utf-8"))
        input_str = ""
        refresh_needed = True
    elif event.name == 'backspace':
        input_str = input_str[:-1]
        refresh_needed = True
    elif event.name == 'space':
        input_str += ' '
        refresh_needed = True
    elif len(event.name) == 1:  # To make sure we only capture printable characters
        input_str += event.name
        refresh_needed = True


class GlobalValues():
    def __init__(self):
        self.connected_addr = None

        self.cl = None


def hoster_ui(port):
    def get_local_ip():
        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            temp_socket.connect(("10.254.254.254", 1))
            local_ip = temp_socket.getsockname()[0]
        except Exception:
            local_ip = '127.0.0.1'
        finally:
            temp_socket.close()
        return local_ip

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    glob_val = GlobalValues()

    def server(port):
        def handle_message():
            while True:
                client, addr = server_socket.accept()
                glob_val.connected_addr = addr
                glob_val.cl = client
                data = client.recv(1024).decode('utf-8')

                if data.lower() == "quit":
                    client.close()
                    add_local_message(f"[ {addr} closed connection ]")
                elif data.lower() == "cn:hello_cs_socket":
                    client.send("cn:response_cs_socket".encode("utf-8"))
                    add_local_message("[ CLIENT CONNECTED ]")
                else:
                    add_local_message(f"> {data}")

        host = get_local_ip()

        server_socket.bind((host, port))

        server_socket.listen(5)

        draw_window_thread = threading.Thread(target=draw_window, args=(host + ":" + str(port),))
        draw_window_thread.daemon = True
        draw_window_thread.start()

        add_local_message("[ ROOM CREATED ]")

        while True:
            client_message_listen_thread = threading.Thread(target=handle_message)
            client_message_listen_thread.start()

    keyboard.on_press(lambda event: on_key_send(event, glob_val.cl))
    server(port)


def connector_ui(addr, port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    glob_val = GlobalValues()

    def listen_for_responses(sock):
        while True:
            response = sock.recv(1024).decode('utf-8')
            if not response:
                add_local_message("[ Nope ]")
                break
            if response == "cn:response_cs_socket":
                glob_val.cl = sock
                add_local_message("[ ROOM ACCEPTED THE CONNECTION ]")
            else:
                add_local_message(f"> {response}")

    def client():
        client_socket.connect((addr, int(port)))

        draw_window_thread = threading.Thread(target=draw_window, args=(addr + ":" + str(port),))
        draw_window_thread.daemon = True
        draw_window_thread.start()

        listen_thread = threading.Thread(target=listen_for_responses, args=(client_socket,))
        listen_thread.start()

        add_local_message("[ ROOM JOINED ]")

        client_socket.send("cn:hello_cs_socket".encode("utf-8"))

    keyboard.on_press(lambda event: on_key_send(event, glob_val.cl))
    client()


def prev_screen():
    response = input("> ")
    if response == "chat":
        print("Creating a chat...")
        port = input("Type the port>  ")
        hoster_ui(int(port))
    elif response == "join":
        address = input("Address>  ")
        port = input("Port> ")
        connector_ui(address, port)
        # message_gui("j", port, address)
    else:
        print("Unknown command...")
        prev_screen()


if __name__ == '__main__':
    print("Unix messenger by H3nry!")
    print("Options [chat, join]")
    prev_screen()
