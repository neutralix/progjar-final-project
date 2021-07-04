import pickle
import socket
import sys
import threading
import string    
import random
import time
from objects import ServMsg, CliMsg

def read_cmd(clients, friend_list, room_list, room_player, sock_cli, addr_cli, username_cli):
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
        elif cmd == "mkroom":
            make_room(clients, room_list, room_player, sock_cli, username_cli)
        elif cmd == "joinroom":
            join_room(clients, room_list, room_player, dest, sock_cli, username_cli)
        elif cmd == "inv":
            invite_room(clients, friend_list, room_list, room_player, dest, sock_cli, username_cli)
        elif cmd == "editw":
            edit_w(clients, room_list, sock_cli, username_cli, msg)
        elif cmd == "editp":
            edit_p(clients, room_list, sock_cli, username_cli, msg)
        elif cmd == "editn":
            edit_n(clients, room_list, sock_cli, username_cli, msg)
        elif cmd == "play":
            play_room(clients, room_list, room_player, sock_cli, username_cli)
        elif cmd == "rlist":
            request_rlist(clients, room_list, room_player, sock_cli, username_cli)
        elif cmd == "rinfo":
            request_rinfo(clients, room_list, room_player, sock_cli, username_cli)
        elif cmd == "leave":
            leave_room(clients, room_list, room_player, sock_cli, username_cli)
        elif cmd == "ans":
            check_ans(clients, room_list, room_player, sock_cli, username_cli, msg)
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
        
        print(msg)
        print(room_list)
        print(room_player)

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
        msg = "Belum berteman dengan {}".format(dest)
        data = pickle.dumps(CliMsg("text", msg))
        sender_sock.send(data)
     
def add_friend(clients, friend_list, dest, sender_sock, username_cli):
    if (username_cli, dest) in friend_list and (dest, username_cli) in friend_list:
        msg = "Kamu sudah berteman dengan {}".format(dest)
        data = pickle.dumps(CliMsg("text", msg))
        sender_sock.send(data)
    elif (username_cli, dest) in friend_list and (dest, username_cli) not in friend_list:
        msg = "Kamu sudah mengirim request ke {}, namun belum diterima".format(dest)
        data = pickle.dumps(CliMsg("text", msg))
        sender_sock.send(data)
    elif (dest, username_cli) in friend_list and (username_cli, dest) not in friend_list:
        msg = "{} sudah melakukan request untuk berteman, 'acc' untuk menerima".format(dest)
        data = pickle.dumps(CliMsg("text", msg))
        sender_sock.send(data)
    else:
        friend_list.add((username_cli, dest))
        # send to sender
        msg = "request dikirim"
        data = pickle.dumps(CliMsg("text", msg))
        sender_sock.send(data)
        # send to receiver
        msg = "{} mengirim kamu request pertemanan".format(username_cli)
        data = pickle.dumps(CliMsg("text", msg))
        clients[dest][0].send(data)
    
    print(friend_list)

def accept_friend(clients, friend_list, dest, sender_sock, username_cli):
    if (username_cli, dest) in friend_list and (dest, username_cli) in friend_list:
        msg = "Kamu sudah berteman dengan {}".format(dest)
        data = pickle.dumps(CliMsg("text", msg))
        sender_sock.send(data)
    elif (dest, username_cli) in friend_list and (username_cli, dest) not in friend_list:
        friend_list.add((username_cli, dest))
        # send to sender
        msg = "Kamu sekarang berteman dengan {}".format(dest)
        data = pickle.dumps(CliMsg("text", msg))
        sender_sock.send(data)
        # send to receiver
        msg = "{} menerima request pertemananmu".format(username_cli)
        data = pickle.dumps(CliMsg("text", msg))
        clients[dest][0].send(data)
    else:
        msg = "Kamu tidak memiliki request pertemanan dari {}".format(dest)
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
    msg = "Kamu tidak lagi berteman dengan {}".format(dest)
    data = pickle.dumps(CliMsg("text", msg))
    sender_sock.send(data)

def send_file(clients, friend_list, dest, sender_sock, username_cli, msg, file_name, file_size, file_data, file_msg):
    #check friend
    if (dest, username_cli) in friend_list and (username_cli, dest) in friend_list:
        data = pickle.dumps(CliMsg("sfile", msg))
        clients[dest][0].send(data)
        clients[dest][0].sendall(file_data)
    else:
        error_msg = "Belum berteman dengan {}".format(dest)
        data = pickle.dumps(CliMsg("text", error_msg))
        sender_sock.send(data)

def make_room(clients, room_list, room_player, sender_sock, username_cli):
    S = 5
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k = S))    

    room_list[code] = [username_cli, sender_sock, 5, 4, 1, 2, 0, -1]
    room_player[code] = []
    room_player[code].append([username_cli, sender_sock, 0])
    msg = "Room berhasil dibuat. Kode {}. Undang temanmu !".format(code)
    data = pickle.dumps(CliMsg("room", msg))
    sender_sock.send(data)

def invite_room(clients, friend_list, room_list, room_player, dest, sender_sock, username_cli):
    if (dest, username_cli) in friend_list and (username_cli, dest) in friend_list:
        sock_cli = clients[dest][0]

        for key in list(room_list.keys()):
            if room_list[key][0] == username_cli:
                code = key
                break

        msg = "<{}>: Gabung room {} untuk bermain dengan saya !".format(username_cli, code)
        data = pickle.dumps(CliMsg("text", msg))
        sock_cli.send(data)
    else:
        msg = "Belum berteman dengan {}".format(dest)
        data = pickle.dumps(CliMsg("text", msg))
        sender_sock.send(data)

def join_room(clients, room_list, room_player, dest, sender_sock, username_cli):
    found = False
    for key in list(room_list.keys()):
        if key == dest:
            found = True
            break
    
    if found == False:
        msg = "Room {} tidak ditemukan".format(dest)
        data = pickle.dumps(CliMsg("text", msg))
        sender_sock.send(data)
    else:
        if (room_list[dest][4] == room_list[dest][3]):
            msg = "Gagal untuk gabung, room {} sudah penuh".format(dest)
            data = pickle.dumps(CliMsg("text", msg))
            sender_sock.send(data)
        elif(room_list[dest][6] == 1):
            msg = "Gagal untuk gabung, room {} sedang bermain".format(dest)
            data = pickle.dumps(CliMsg("text", msg))
            sender_sock.send(data)
        else:
            room_player[dest].append([username_cli, sender_sock, 0])
            room_list[dest][4] += 1
            msg = "Berhasil gabung room {}".format(dest)
            data = pickle.dumps(CliMsg("room", msg))
            sender_sock.send(data)

def play_room(clients, room_list, room_player, sock_cli, username_cli):
    found = False
    for key in list(room_list.keys()):
        if room_list[key][0] == username_cli:
            code = key
            room_list[code][6] = 1
            msg  = "\nPermainan Dimulai!\n"
            msg =  pickle.dumps(CliMsg("play",msg))
            for player in room_player[code]:
                player[1].send(msg) 
            generate(code)
            found = True
            break

    if found == False:
        msg = "Kamu bukan room master"
        data = pickle.dumps(CliMsg("text", msg))
        sock_cli.send(data)
    
def generate(code):
    answer = 0
    if room_list[code][5] == 2:
        operator = random.randint(0, 3)
        a = random.randint(1, 300)
        b = random.randint(1, 300)
        c = random.randint(1, 15)
        d = random.randint(1, 10)
        if operator == 0:
            question = "{} + {} = ?".format(a, b)
            answer = a + b
        elif operator == 1:
            question = "{} - {} = ?".format(a, b)
            answer = a - b
        elif operator == 2:
            question = "{} x {} = ?".format(c, d)
            answer = c * d
        elif operator == 3:
            question = "{} / {} = ?".format(a, d)
            answer = a / d
            while (a/d != a//d):
                a = random.randint(1, 300)
                question = "{} / {} = ?".format(a, d)
                answer = a / d
    elif room_list[code][5] == 3:
        operator  = random.randint(0, 3)
        a = random.randint(1, 300)
        b = random.randint(1, 300)
        c = random.randint(1, 15)
        d = random.randint(1, 10)
        if operator == 0:
            question = "{} + {}".format(a, b)
            answer = a + b
        elif operator == 1:
            question = "{} - {}".format(a, b)
            answer = a - b
        elif operator == 2:
            question = "{} x {}".format(c, d)
            answer = c * d
        elif operator == 3:
            question = "{} / {}".format(a, d)
            answer = a / d
            while (a/d != a//d):
                a = random.randint(1, 300)
                question = "{} / {}".format(a, d)
                answer = a / d
    
        operator  = random.randint(0, 1)
        c = random.randint(1, 300)
        if operator == 0:
            question = "{} + {} = ?".format(question, c)
            answer = answer + c
        elif operator == 1:
            question = "{} - {} = ?".format(question, c)
            answer = answer - c
        
    ans = int(answer)
    print(ans)
    room_list[code][7] = ans
    
    send_player(code,question)

def send_player(code, question):
    time.sleep(1) 
    ldb  = "\nPapan Skor\n"
    for player in room_player[code]:
        ldb += "{} punya {} poin\n".format(player[0], player[2])
    
    ldb =  pickle.dumps(CliMsg("text",ldb))
    for player in room_player[code]:
        player[1].send(ldb)   
    
    time.sleep(1) 
    
    msg = "Berapakah hasil {}".format(question)
    data = pickle.dumps(CliMsg("text", msg))
    for player in room_player[code]:
        player[1].send(data)

def check_ans(clients, room_list, room_player, sock_cli, username_cli, msg):
    isWin = False
    code = ''
    found = False
    for key in list(room_player.keys()):
        if found == True:
            break
        for player in room_player[key]:
            if player[0] == username_cli:
                code = key
                found = True
                break

    ans = int(msg)
    print("ans = {}".format(room_list[code][7]))
    
    if(ans == room_list[code][7]):
        for player in room_player[code]:
            if player[0] == username_cli:
                player[2] += 1
                if player[2] == room_list[code][2]:
                    isWin = True
                break

        if isWin == True:
            msg = "{} Menang !".format(username_cli)
            data = pickle.dumps(CliMsg("win", msg))
            room_list[code][6] = 0
            for player in room_player[code]:
                player[2] = 0
                player[1].send(data)
        else:
            msg = "{} berhasil menjawab dengan benar !".format(username_cli)
            data = pickle.dumps(CliMsg("text", msg))
            for player in room_player[code]:
                if player[0] == username_cli:
                    msg = "Jawaban Benar!"
                    msg = pickle.dumps(CliMsg("text", msg))
                    player[1].send(msg)
                else:
                    player[1].send(data)
            generate(code)
    else:
        msg = "Jawaban Salah!"
        data = pickle.dumps(CliMsg("text", msg))
        sock_cli.send(data)

def edit_w(clients, room_list, sock_cli, username_cli, msg):
    found = False
    for key in list(room_list.keys()):
        if room_list[key][0] == username_cli:
            room_list[key][2] = int(msg)
            found = True
            break

    if found == False:
        msg = "Kamu bukan room master"
        data = pickle.dumps(CliMsg("text", msg))
        sock_cli.send(data)

def edit_p(clients, room_list, sock_cli, username_cli, msg):
    found = False
    for key in list(room_list.keys()):
        if room_list[key][0] == username_cli:
            room_list[key][3] = int(msg)
            found = True
            break

    if found == False:
        msg = "Kamu bukan room master"
        data = pickle.dumps(CliMsg("text", msg))
        sock_cli.send(data)
    

def edit_n(clients, room_list, sock_cli, username_cli, msg):
    found = False
    for key in list(room_list.keys()):
        if room_list[key][0] == username_cli:
            room_list[key][5] = int(msg)
            found = True
            break

    if found == False:
        msg = "Kamu bukan room master"
        data = pickle.dumps(CliMsg("text", msg))
        sock_cli.send(data)

def request_rlist(clients, room_list, room_player, sock_cli, username_cli):
    code = ''
    found = False
    for key in list(room_player.keys()):
        if found == True:
            break
        for player in room_player[key]:
            if player[0] == username_cli:
                code = key
                found = True
                break
    
    rlist  = "\nPemain\n"
    number = 1
    for player in room_player[code]:
        rlist += "{} | {} \n".format(number, player[0])
        number += 1

    data = pickle.dumps(CliMsg("text", rlist))
    sock_cli.send(data)

def request_rinfo(clients, room_list, room_player, sock_cli, username_cli):
    code = ''
    found = False
    for key in list(room_player.keys()):
        if found == True:
            break
        for player in room_player[key]:
            if player[0] == username_cli:
                code = key
                found = True
                break

    rinfo  = "\nInformasi Room\n" +\
            "Jumlah Poin  Untuk Menang : {}\n".format(room_list[key][2]) +\
            "Jumlah Angka Pada Soal : {}\n".format(room_list[key][5]) +\
            "Jumlah Maksimum Pemain : {}\n".format(room_list[key][3])
    data = pickle.dumps(CliMsg("text", rinfo))
    sock_cli.send(data)

def leave_room(clients, room_list, room_player, sock_cli, username_cli):
    code = ''
    found = False
    for key in list(room_player.keys()):
        if found == True:
            break
        for player in room_player[key]:
            if player[0] == username_cli:
                code = key
                found = True
                break

    if (room_list[code][0] == username_cli):
        warning = "Room master meninggalkan room. Room dibubarkan\n"
        warning = pickle.dumps(CliMsg("menu", warning))
        for player in room_player[code]:
            player[1].send(warning)
        
        room_list.pop(code)
        room_player.pop(code)
    else:
        for player in room_player[key]:
            if player[0] == username_cli:
                room_player[key].remove(player)
                
        msg = "Kamu sudah keluar dari room\n"
        msg = pickle.dumps(CliMsg("menu", msg))    
        sock_cli.send(msg)

sock_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_server.bind(("0.0.0.0", 6666))
sock_server.listen(5)

clients = {}

# room_list[kode] = {username masternya, socket_master, point menang(integer),maks orang(integer), jumlah orng yg ad(int),
# banyak variabel(integer), LAGI PLAY/LAGI NUNGGU(boolean), CURRENT ANSWER(integer)}
room_list = {}

# room_player[kode] = {(username pemain, socket pemain, point brp, ),  (), ()}
# player = [username pemain, socket pemain, point brp]
room_player = {}

friend_list = set()

while True:
    sock_cli, addr_cli = sock_server.accept()

    username_cli = sock_cli.recv(65535).decode("utf-8")
    print(username_cli, " joined")

    thread_cli = threading.Thread(target=read_cmd, args=(clients, friend_list, room_list, room_player, sock_cli, addr_cli, username_cli))
    thread_cli.start() 

    clients[username_cli] = (sock_cli, addr_cli, thread_cli)