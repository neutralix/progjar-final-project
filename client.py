import pickle
import socket
import sys
import threading
import os
from objects import ServMsg, CliMsg

def read_msg(sock_cli):
    while True:
        global player_status
        global new_status
        data = sock_cli.recv(65535)
        obj = pickle.loads(data)

        # print(obj.dtype)
        # print(obj.msg)
        
        header = obj.dtype
        msg = obj.msg

        if len(data) == 0:
            break
        
        if header == "rfile":
            filemsg = msg.split("|", 2)
            file_name = filemsg[0]
            file_size = int(filemsg[1])
            file_msg = filemsg[2]
            with open(file_name, "rb") as f:
                file_data = f.read()

            sock_cli.sendall(file_data)
        elif header == "sfile":
            filemsg = msg.split("|", 2)
            file_name = filemsg[0]
            file_size = int(filemsg[1])
            file_msg = filemsg[2]

            with open(file_name, "wb") as f:
                file_data = sock_cli.recv(65535)
                f.write(file_data)
                while (file_size - len(file_data) > 0):
                    data = sock_cli.recv(65535)
                    file_data += data
                    f.write(data)
            print("menerima file {}".format(file_name))
        elif header == "text":
            if isinstance(msg, list):
                print("Friend List :")
                print(*msg, sep = "\n")
            else:
                print(msg)
        elif header == "room":
            player_status = 1
            new_status = 1
            print(msg)
            command_info()
        elif header == "play":
            player_status = 2
            new_status = 1
            print(msg)
            command_info()
        elif header == "win":
            player_status = 1
            new_status = 1
            print(msg)
            command_info()
        elif header == "menu":
            player_status = 0
            new_status = 1
            print(msg)
            command_info()

def command_info():
    global player_status
    global new_status
    if player_status == 0 and new_status == 1:
        print("<command list>\n"\
                "bcast -> broadcast pesan ke semua teman\n"\
                "msg -> kirim pesan private ke teman\n"\
                "add -> request untuk jadi teman\n"\
                "acc -> terima permintaan teman\n"\
                "flist -> lihat daftar teman\n"\
                "rm -> hapus teman\n"\
                "file -> kirim file ke teman\n"\
                "mkroom -> buat room permainan\n"\
                "joinroom -> gabung room permainan\n"\
                "exit -> tutup program\n")
    elif player_status == 1 and new_status == 1:
        print("<room command list>\n"\
                "[room master]\n"
                "play -> mulai permainan\n"\
                "editw -> ubah jumlah point untuk menang\n"
                "editp -> ubah jumlah maksimum pemain\n"\
                "editn -> ubah jumlah angka yang muncul [pilihan: 2, 3]\n"\
                "inv -> undang temanmu ke dalam room\n"
                "[all player]\n"\
                "rlist -> lihat daftar pemain dalam room\n"\
                "rinfo -> lihat setting room permainan\n"
                "leave -> keluar dari room\n")
    elif player_status == 2 and new_status == 1:
        print("<play command list>\n"\
                "ans -> jawab pertanyaan\n")
    new_status = 0

# check input username
if len(sys.argv) != 2:
    sys.exit()

sock_cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_cli.connect(("127.0.0.1", 6666))
sock_cli.send(bytes(sys.argv[1], "utf-8"))

thread_cli = threading.Thread(target=read_msg, args=(sock_cli,))
thread_cli.start()

file_data = b''
player_status = 0
new_status = 1

print("\n##############")
print("#    MATH    #")
print("#    RUSH    #")
print("##############\n")

while True:
    if new_status == 1:
        command_info()

    # input command
    cmd = input(">>> ")
    
    # cmd = command.split(' ', 1)[0]
    # print(command.split(' ', 1))

    if cmd == "bcast":
        dest = "bcast"
        msg = input("masukan pesan : ")
    elif cmd == "msg":
        dest = input("masukan username tujuan : ")
        msg = input("masukan pesan: ")
    elif cmd == "add":
        dest = input("masukan username untuk request friend : ")
        msg = "request friend"
    elif cmd == "acc":
        dest = input("masukan username untuk accept friend : ")
        msg = "accept friend"
    elif cmd == "flist":
        dest = sys.argv[1]
        msg = "request friend list"
    elif cmd == "rm":
        dest = input("masukan username untuk unfriend : ")
        msg = "remove friend"    
    elif cmd == "file":
        dest = input("masukan username tujuan : ")
        file_name = input("masukan nama file : ")
        msg = "mengirim file"
    elif cmd == "mkroom":
        if player_status == 1:
            print("Kamu sudah berada dalam room !")
            continue
        elif player_status == 2:
            print("Kamu sedang bermain !")
            continue
        
        dest = "mkroom"
        msg = "mkroom"
    elif cmd == "joinroom":
        if player_status != 0:
            print("Kamu sedang berada dalam room !")
            continue
            
        dest = input("masukan kode room tujuan : ")
        msg = "join to room"
    elif cmd == "inv":
        if player_status == 0:
            print("Kamu tidak sedang berada dalam room !")
            continue
        elif player_status == 2:
            print("Kamu sedang bermain !")
            continue
        
        dest = input("masukan username teman yang ingin diundang : ")
        msg = "invite friend to room"
    elif cmd == "play":
        if player_status == 0:
            print("Kamu tidak sedang berada dalam room !")
            continue
        elif player_status == 2:
            print("Kamu sedang bermain !")
            continue
            
        dest ="play"
        msg = "play"
    elif cmd == "editw":
        if player_status == 0:
            print("Kamu tidak sedang berada dalam room !")
            continue
        elif player_status == 2:
            print("Kamu sedang bermain !")
            continue
            
        dest = "editw"
        msg = input("masukan jumlah point untuk menang : ")
        while (int(msg) < 1):
            print("jumlah point untuk menang minimal 1\n")
            msg = input("masukan jumlah point untuk menang : ")
    elif cmd == "editp":
        if player_status == 0:
            print("Kamu tidak sedang berada dalam room !")
            continue
        elif player_status == 2:
            print("Kamu sedang bermain !")
            continue
            
        dest = "editp"
        msg = input("masukan jumlah maksimum pemain : ")
    elif cmd == "editn":
        if player_status == 0:
            print("Kamu tidak sedang berada dalam room !")
            continue
        elif player_status == 2:
            print("Kamu sedang bermain !")
            continue

        dest = "editn"
        msg = input("masukan jumlah angka yang muncul (2-3) : ")
        while (int(msg) > 3 or int(msg) < 2):
            print("jumlah angka tidak sesuai, jumlah angka minimal adalah 2 dan maksimal 3\n")
            msg = input("masukan jumlah angka yang muncul (2-3) : ")
    elif cmd == "ans":
        if player_status == 0:
            print("Kamu tidak sedang bermain !")
            continue
        elif player_status == 1:
            print("Kamu tidak sedang bermain !")
            continue
            
        dest = "ans"
        msg = input("masukan jawaban : ")
    elif cmd == "rlist":
        if player_status == 0:
            print("Kamu tidak sedang berada dalam room !")
            continue

        dest = "rlist"
        msg = "check room list"
    elif cmd == "rinfo":
        if player_status == 0:
            print("Kamu tidak sedang berada dalam room !")
            continue

        dest = "rinfo"
        msg = "check room info"
    elif cmd == "leave":
        if player_status == 0:
            print("Kamu tidak sedang berada dalam room !")
            continue
        elif player_status == 2:
            print("Kamu sedang bermain !")
            continue

        dest = "leave"
        msg = "leave room"
    elif cmd == "exit":
        if player_status == 1:
            print("Kamu sedang berada dalam room !")
            continue
        elif player_status == 2:
            print("Kamu sedang bermain !")
            continue

        sock_cli.close()
        break
    else:
        print("command not found")
        continue

    if cmd == "file":
        if not os.path.exists(file_name):
            print('File tidak ditemukan.')
            continue

        file_size = 0
        with open(file_name, "rb") as f:
            file_data = f.read()
            file_size += len(file_data)
        
        msg = "{}|{}|{}".format(file_name, file_size, msg)
        data = pickle.dumps(ServMsg(cmd, dest, msg))
        sock_cli.send(data)
    else:
        data = pickle.dumps(ServMsg(cmd, dest, msg))
        sock_cli.send(data)
        