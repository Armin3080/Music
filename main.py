import sys,os
from colorama import Fore
import time
#next
#color
red='\033[31m'
green='\033[32m'
blue='\033[36m'
pink='\033[35m'
orange = '\033[1;31m'
# next
if os.name == 'nt':
    os.system('cls')
else:
    os.system('clear')
#next
print(f"{red}                                               [                    ] 0% ")
time.sleep(1.5)
if os.name == 'nt':
    os.system('cls')
else:
    os.system('clear')
print(f"{red}                                               [=====               ] 25%")
time.sleep(1.5)
if os.name == 'nt':
    os.system('cls')
else:
    os.system('clear')
print(f"{orange}                                            [==========          ] 50%")
time.sleep(1.5)
if os.name == 'nt':
    os.system('cls')
else:
    os.system('clear')
print(f"{green}                                             [===============     ] 75%")
time.sleep(1.5)
if os.name == 'nt':
    os.system('cls')
else:
    os.system('clear')
print(f"{green}                                             [====================] 100%")
time.sleep(1)
if os.name == 'nt':
    os.system('cls')
else:
    os.system('clear')
print(f"""{blue}
                     
 ▓█████▄      ▒█████       ▄████▄      ▀██ ▄█▀    ▄▄▄█████▓    ▓██   ██▓     ██▓███      ▓█████
 ▒██▀ ██▌    ▒██▒  ██▒    ▒██▀ ▀█       ██▄█▒     ▓  ██▒ ▓▒     ▒██  ██▒    ▓██░  ██     ▓█   ▀
 ░██   █▌    ▒██░  ██▒    ▒▓█    ▄     ▓███▄░     ▒ ▓██░ ▒░      ▒██ ██░    ▓██░ ██▓▒    ▒███  
▒░▓█▄   ▌    ▒██   ██░    ▒▓▓▄ ▄██     ▓██ █▄     ░ ▓██▓ ░       ░ ▐██▓░    ▒██▄█▓▒ ▒    ▒▓█  ▄
░░▒████▓     ░ ████▓▒░    ▒ ▓███▀      ▒██▒ █▄      ▒██▒ ░       ░ ██▒▓░    ▒██▒ ░  ░    ░▒████
░ ▒▒▓  ▒     ░ ▒░▒░▒░     ░ ░▒ ▒       ▒ ▒▒ ▓▒      ▒ ░░          ██▒▒▒     ▒▓▒░ ░  ░    ░░ ▒░ 
  ░ ▒  ▒       ░ ▒ ▒░       ░  ▒       ░ ░▒ ▒░        ░         ▓██ ░▒░     ░▒ ░          ░ ░  
  ░ ░  ░     ░ ░ ░ ▒      ░            ░ ░░ ░       ░ ░         ▒ ▒ ░░      ░░              ░  
    ░            ░ ░      ░ ░          ░  ░                     ░ ░                         ░  
      
                              
          
           """)

def display_menu():
    print(f"""
    {green}―――――――――――――――――――――――――――――――――――――――――――――――――――――――
    {red}|1| {green}Ddos 1 (noemal)          {red}|2| {green}Ddos 2(weak)
    {red}|3| {green}Ddos 3 (powerful)                                                     
    {green}―――――――――――――――――――――――――――――――――――――――――――――――――――――――
    """)
def execute_command(command):
    if command == '1':
        os.system('python ddos.py')
    elif command == '2':
        os.system('python dos.py')
    elif command == '3':
        os.system('python predator.py')


while True:
    display_menu()
    command = input('>>>>>>')

    if command.lower() == 'exit':
        break

    execute_command(command)