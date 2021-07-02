import pickle
import socket
import sys
import threading
import string    
import random
from objects import ServMsg, CliMsg

def read_cmd(clients, friend_list, sock_cli, addr_cli, username_cli):
    while True:
        data = sock_cli.recv(65535)
        if len(data) == 0:
            break
            
        obj = pickle.loads(data)
        
        cmd = obj.cmd
        dest = obj.dest
        msg = obj.msg

        if cmd == "bcast":
            msg = "<{}>: {}".format(username_cli, msg)
            send_broadcast(clients, friend_list, addr_cli, username_cli, msg)
        elif cmd == "msg":
            msg = "<{}>: {}".format(username_cli, msg)
            send_msg(clients, friend_list, dest, sock_cli, username_cli, msg)
        elif cmd == "add":
            add_friend(clients, friend_list, dest, sock_cli, username_cli)
        elif cmd == "acc":
            accept_friend(clients, friend_list, dest, sock_cli, username_cli)
        elif cmd == "flist":
            request_flist(clients, friend_list, sock_cli, username_cli)
        elif cmd == "rm":
            remove_friend(clients, friend_list, dest, sock_cli, username_cli)
        elif cmd == "file":
            filemsg = msg.split("|", 2)
            file_msg = filemsg[2]
            file_name = filemsg[0]
            file_size = int(filemsg[1])

            data = pickle.dumps(CliMsg("rfile", msg))
            sock_cli.send(data)

            file_data = sock_cli.recv(65535)
            while (file_size - len(file_data) > 0):
                data = sock_cli.recv(65535)
                file_data += data

            send_file(clients, friend_list, dest, sock_cli, username_cli, msg, file_name, file_size, file_data, file_msg)
        
    sock_cli.close()
    print("Connection closed", addr_cli)

def send_broadcast(clients, friend_list, sender_addr_cli, username_cli, msg):
    for key in list(clients.keys()):
        if not (sender_addr_cli[0] == clients[key][1][0] and sender_addr_cli[1] == clients[key][1][1]):
            if (key, username_cli) in friend_list and (username_cli, key) in friend_list:
            data = pickle.dumps(CliMsg("text", msg))
            clients[key][0].send(data)
   
def send_msg(clients, friend_list, dest, sender_sock, username_cli, msg):
    #check friend
    if (dest, username_cli) in friend_list and (username_cli, dest) in friend_list:
        sock_cli = clients[dest][0]
        
        data = pickle.dumps(CliMsg("text", msg))
        sock_cli.send(data)
    else:
        msg = "not friend with {}".format(dest)
        data = pickle.dumps(CliMsg("text", msg))
        sender_sock.send(data)
     
def add_friend(clients, friend_list, dest, sender_sock, username_cli):
    if (username_cli, dest) in friend_list and (dest, username_cli) in friend_list:
        msg = "already friend with {}".format(dest)
        data = pickle.dumps(CliMsg("text", msg))
        sender_sock.send(data)
    elif (username_cli, dest) in friend_list and (dest, username_cli) not in friend_list:
        msg = "already request friend to {}, but still not accepted".format(dest)
        data = pickle.dumps(CliMsg("text", msg))
        sender_sock.send(data)
    elif (dest, username_cli) in friend_list and (username_cli, dest) not in friend_list:
        msg = "{} already request to be friend with you, use 'acc' command to accept".format(dest)
        data = pickle.dumps(CliMsg("text", msg))
        sender_sock.send(data)
    else:
        friend_list.add((username_cli, dest))
        # send to sender
        msg = "request sent"
        data = pickle.dumps(CliMsg("text", msg))
        sender_sock.send(data)
        # send to receiver
        msg = "{} send you a friend request".format(username_cli)
        data = pickle.dumps(CliMsg("text", msg))
        clients[dest][0].send(data)
    
    print(friend_list)

def accept_friend(clients, friend_list, dest, sender_sock, username_cli):
    if (username_cli, dest) in friend_list and (dest, username_cli) in friend_list:
        msg = "already friend with {}".format(dest)
        data = pickle.dumps(CliMsg("text", msg))
        sender_sock.send(data)
    elif (dest, username_cli) in friend_list and (username_cli, dest) not in friend_list:
        friend_list.add((username_cli, dest))
        # send to sender
        msg = "you are now friend with {}".format(dest)
        data = pickle.dumps(CliMsg("text", msg))
        sender_sock.send(data)
        # send to receiver
        msg = "{} accepted your friend request".format(username_cli)
        data = pickle.dumps(CliMsg("text", msg))
        clients[dest][0].send(data)
    else:
        msg = "you have no friend request from {}".format(dest)
        data = pickle.dumps(CliMsg("text", msg))
        sender_sock.send(data)

def request_flist(clients, friend_list, sender_sock, username_cli):
    flist = []

    for (a, b) in friend_list:
        if(a == username_cli):
            flist.append(b)

    data = pickle.dumps(CliMsg("text", flist))
    sender_sock.send(data)

def remove_friend(clients, friend_list, dest, sender_sock, username_cli):
    friend_list.remove((username_cli, dest))
    friend_list.remove((dest, username_cli))
    msg = "you are no longer friend with {}".format(dest)
    data = pickle.dumps(CliMsg("text", msg))
    sender_sock.send(data)

def send_file(clients, friend_list, dest, sender_sock, username_cli, msg, file_name, file_size, file_data, file_msg):
    #check friend
    if (dest, username_cli) in friend_list and (username_cli, dest) in friend_list:
        data = pickle.dumps(CliMsg("sfile", msg))
        clients[dest][0].send(data)
        clients[dest][0].sendall(file_data)
    else:
        error_msg = "Not friend with {}".format(dest)
        data = pickle.dumps(CliMsg("text", error_msg))
        sender_sock.send(data)

sock_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_server.bind(("0.0.0.0", 6666))
sock_server.listen(5)

clients = {}
friend_list = set()

while True:
    sock_cli, addr_cli = sock_server.accept()

    username_cli = sock_cli.recv(65535).decode("utf-8")
    print(username_cli, " joined")

    thread_cli = threading.Thread(target=read_cmd, args=(clients, friend_list, sock_cli, addr_cli, username_cli))
    thread_cli.start() 

    clients[username_cli] = (sock_cli, addr_cli, thread_cli)