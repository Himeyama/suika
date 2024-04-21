import argparse
import socket
import click
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import socket
import sys
import threading
import re
import pandas as pd

def get_cpu_info(txt: str):
    pattern = r"%Cpu(\d+)\s+:\s+(\d+\.?\d+)\s+us,\s*(\d+\.?\d+)\s+sy,\s*(\d+\.?\d+)\s+ni,\s*(\d+\.?\d+)\s+id,\s*(\d+\.?\d+)\s+wa,\s*(\d+\.?\d+)\s+hi,\s*(\d+\.?\d+)\s+si,\s*(\d+\.?\d+)\s+st"
    match = re.match(pattern, txt)
    if match:
        return pd.Series([float(match.group(i)) for i in range(2, 10)], ["us", "sy", "ni", "id", "wa", "hi", "si", "st"])
    else:
        return None
    
def read_top1(txt: str):
    flag = False
    cpus = []
    for line in txt.split("\n"):
        cpu_info = get_cpu_info(line)
        if cpu_info is not None:
            flag = True
            cpus.append(cpu_info)
        if cpu_info is None and flag: break
    df = pd.DataFrame(cpus)
    try:
        df["usage"] = 100 - (df["ni"] + df["id"])
    except KeyError:
        print(df)

    return df


def read_top1_col2(txt: str):
    cpus = []
    for line in txt.split("\n"):
        pattern: str = r"%Cpu(\d+)\s*:\s*(\d+\.?\d+)\s+us,\s*(\d+\.?\d+)\s+sy,\s*(\d+\.?\d+)\s+ni,\s*(\d+\.?\d+)\s+id,\s*(\d+\.?\d+)\s+wa,\s*(\d+\.?\d+)\s+hi,\s*(\d+\.?\d+)\s+si,\s*(\d+\.?\d+)\s+st\s+%Cpu(\d+)\s*:\s*(\d+\.?\d+)\s+us,\s*(\d+\.?\d+)\s+sy,\s*(\d+\.?\d+)\s+ni,\s*(\d+\.?\d+)\s+id,\s*(\d+\.?\d+)\s+wa,\s*(\d+\.?\d+)\s+hi,\s*(\d+\.?\d+)\s+si,\s*(\d+\.?\d+)\s+st"
        match = re.match(pattern, line)
        # print(line)
        if match:
            cpu1, us1, sy1, ni1, id1, wa1, hi1, si1, st1 = [float(match.group(col)) for col in range(1, 10)]
            cpu2, us2, sy2, ni2, id2, wa2, hi2, si2, st2 = [float(match.group(col)) for col in range(10, 19)]
            cpu1 = int(cpu1)
            cpu2 = int(cpu2)
            series1 = pd.Series([us1, sy1, ni1, id1, wa1, hi1, si1, st1], index=["us", "sy", "ni", "id", "wa", "hi", "si", "st"])
            series2 = pd.Series([us2, sy2, ni2, id2, wa2, hi2, si2, st2], index=["us", "sy", "ni", "id", "wa", "hi", "si", "st"])
            cpus.append(series1)
            cpus.append(series2)
    df = pd.DataFrame(cpus)
    try:
        df["usage"] = 100 - (df["ni"] + df["id"])
    except KeyError:
        print(df)
    return df

# a = 0
graph_data = None # Core = 24
server_kill = False
exit_flag = False

def p(count: int):
    global server_kill

    def clear_plot():
        if exit_flag: exit(False)

        grid_color = "#F6F6F6"
        for i, axl in enumerate(axs):
            for j, ax in enumerate(axl):
                ax.clear()

                ax.tick_params(bottom=False, left=False, labelbottom=False, labelleft=False)
                for spine in ax.spines.values():
                    spine.set_edgecolor(grid_color)
                ax.set_xticks([0, 20, 40, 60])
                ax.set_xlim([0, 60])
                ax.set_yticks(range(0, 101, 10))
                ax.set_ylim([0, 100])
                ax.set_axisbelow(True)
                ax.grid(True, color=grid_color)

    def plot(n: int):
        global graph_data
        
        clear_plot()

        for i, axl in enumerate(axs):
            for j, ax in enumerate(axl):
                if graph_data is not None:
                    ax.plot(graph_data[:, i * axs.shape[1] + j], lw=1, color="#90C2DF")
                    ax.fill_between(np.arange(0, 61, 1), graph_data[:, i * axs.shape[1] + j], color="#90C2DF", alpha=0.2)                

    # print(graph_data)
    if count == 2:
        fig, axs = plt.subplots(1, 2)
        axs = axs.reshape(1, 2)
    elif count == 4:
        fig, axs = plt.subplots(2, 2)
    elif count == 6:
        fig, axs = plt.subplots(2, 3)
    elif count == 8:
        fig, axs = plt.subplots(2, 4)
    elif count == 12:
        fig, axs = plt.subplots(3, 4)
    elif count == 12:
        fig, axs = plt.subplots(3, 4)
    elif count == 24:
        fig, axs = plt.subplots(4, 6)

    clear_plot()
    fig.subplots_adjust(hspace=0.05, wspace=0.05)
    anim = animation.FuncAnimation(fig, plot, interval=500, cache_frame_data=False)
    plt.show()
    server_kill = True

def server(n_cpu: int):
    global graph_data
    global server_kill
    global exit_flag

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_socket.bind(('localhost', 8080))
    except OSError as err:
        print(f"OSError: {err}")
        server_socket.close()
        exit_flag = True
        sys.exit(False)

    server_socket.listen(1)

    graph_data = np.zeros((61, n_cpu))
    while True:
        try:
            client_socket, addr = server_socket.accept()
        except KeyboardInterrupt:
            print("Ctrl+C を検知しました")
            server_socket.close()
            exit_flag = True
            sys.exit()

        if server_kill:
            print("終了を検知しました")
            server_socket.close()
            exit_flag = True
            sys.exit()

        data = client_socket.recv(65535)
        msg = data.decode('utf-8')
        df = read_top1_col2(msg)
        print(df)

        try:
            new_line = df["usage"].to_numpy().reshape(1, -1)
        except:
            pass

        try:
            graph_data = np.vstack([graph_data[1:, :], new_line])
        except:
            pass
        
        client_socket.close()


@click.command()
@click.option("-c", "--core", type=int, default=24, help="回数")
def suika(core):
    th1 = threading.Thread(target=server, args=(core,))
    th1.start()

    p(core)
    th1.join()
