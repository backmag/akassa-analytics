import tkinter as tk 
from tkinter import ttk
import matplotlib
matplotlib.use("TkAgg")
matplotlib.rc('lines', linewidth=0.5)
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style
style.use("ggplot")
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker

import urllib
import json
import os
import requests
import pickle

import bs4 as bs
from pathlib import Path
from datetime import datetime

import pandas as pd
import pandas_datareader.data as web
pd.plotting.register_matplotlib_converters() # For plotting dates with matplotlib
import numpy as np


LARGE_FONT = ("Avenir", 12)
MID_FONT = ("Avenir", 10)
SMALL_FONT = ("Avenir", 8)

MAIN_COLORS = ["#0093b2","#00547a", "#83a05d", "#848283", "#c9beb4"]
SMA_COLORS = ["#ff0000", "#f88fa7","#a38b14"]
EMA_COLORS = ["#0013ff","#2e8855","#00ffe4"]


DATAHANDLER = None 



f = plt.figure()

# Global variables 
startDate = datetime(2018,1,1)
endDate = datetime.today() 
topIndicator = "none"
midIndicators = "none"
lowIndicator = "none"
currentTickers = ['AAPL'] # Just a standard starting-ticker to show. 

reloadQueued = True

def addBottomIndicator(name): 
	global bottomIndicator
	global globalCounter

	if name == 'none': 
		bottomIndicator = 'none'
		globalCounter = 9000
	elif name == 'rsi': 
		rsiQ = tk.Tk()
		rsiQ.wm_title('Set parameter')
		label = ttk.Label(rsiQ, text = "Choose how many periods you want each RSI calculation to consider.")
		label.pack(side="top", fill="x", pady=10)

		e = ttk.Entry(rsiQ)
		e.insert(0,14)
		e.pack()
		e.focus_set()

		def callback(): 
			global bottomIndicator
			global globalCounter

			periods = (e.get())
			group = []
			group.append("rsi")
			group.append(periods) 

			bottomIndicator = group
			globalCounter = 9000
			print("Set bottom indicator to:", group)
			rsiQ.destroy()

		b = ttk.Button(rsiQ, text="Submit", width=10, command=callback)
		b.pack()
		tk.mainloop()

	elif name == "macd":
		bottomIndicator = "macd"
		globalCounter = 9000


def addMidIndicators(name): 
	global midIndicators
	global reloadQueued

	if not name == "none": 
		if midIndicators == "none": 
			if name == "sma":
				midIQ = tk.Tk() 
				midIQ.wm_title('Set parameter')
				midIQ.iconbitmap("./img/widget.ico")
				label = ttk.Label(midIQ, text="Choose a window size for the SMA.")
				label.pack(side="top", fill="x", pady=10, padx=30)
				e = ttk.Entry(midIQ) 
				e.insert(0, 10)
				e.pack()
				e.focus_set() 
				def callback(): 
					global midIndicators
					global reloadQueued

					midIndicators = []
					periods = (e.get())
					group = []
					group.append('sma')
					group.append(int(periods))
					midIndicators.append(group)
					globalCounter = 9000
					reloadQueued = True
					midIQ.destroy()

				b = ttk.Button(midIQ, text="Submit", width=10, command=callback)
				b.pack()
				tk.mainloop()

			if name == "ema":
				midIQ = tk.Tk() 
				midIQ.wm_title('Set parameter')
				midIQ.iconbitmap("./img/widget.ico")
				label = ttk.Label(midIQ, text="Choose a smoothing factor alpha between 0 and 1.")
				label.pack(side="top", fill="x", pady=10, padx=10)
				e = ttk.Entry(midIQ) 
				e.insert(0, 0.5)
				e.pack()
				e.focus_set() 
				def callback(): 
					global midIndicators
					global reloadQueued

					midIndicators = []
					alpha = float(e.get())
					if alpha < 0 or alpha > 1: 
						popupmsg("Alpha must be between 0 and 1.")
					else: 
						group = []
						group.append('ema')
						group.append(alpha)
						midIndicators.append(group)
						globalCounter = 9000
						reloadQueued = True
						midIQ.destroy()

				b = ttk.Button(midIQ, text="Submit", width=10, command=callback)
				b.pack()
				tk.mainloop()
		else: 
			if name == "sma": 
				midIQ = tk.Tk() 
				midIQ.wm_title('Set parameter')
				midIQ.iconbitmap("./img/widget.ico")
				label = ttk.Label(midIQ, text="Choose a window size for the SMA.")
				label.pack(side="top", fill="x", pady=10, padx=30)
				e = ttk.Entry(midIQ) 
				e.insert(0, 10)
				e.pack()
				e.focus_set() 
				def callback(): 
					global midIndicators
					global reloadQueued

					periods = (e.get())
					if not ['sma', int(periods)] in midIndicators: 
						group = []
						group.append('sma')
						group.append(int(periods))
						midIndicators.append(group)
						reloadQueued = True
						midIQ.destroy()
					else: 
						midIQ.destroy()
						popupmsg("You already have that window.")

				b = ttk.Button(midIQ, text="Submit", width=10, command=callback)
				b.pack()
				tk.mainloop()
			elif name == "ema":
				midIQ = tk.Tk() 
				midIQ.wm_title('Set parameter')
				midIQ.iconbitmap("./img/widget.ico")
				label = ttk.Label(midIQ, text="Choose a smoothing factor alpha between 0 and 1.")
				label.pack(side="top", fill="x", pady=10, padx=10)
				e = ttk.Entry(midIQ) 
				e.insert(0, 0.5)
				e.pack()
				e.focus_set() 
				def callback():
					global midIndicators
					global reloadQueued

					alpha = float(e.get())
					if alpha < 0 or alpha > 1: 
						popupmsg("Alpha must be between 0 and 1.")
					elif not ['ema', alpha] in midIndicators: 
						group = []
						group.append('ema')
						group.append(alpha)
						midIndicators.append(group)
						reloadQueued = True
						midIQ.destroy()
					else: 
						popupmsg("You already have that alpha.")

				b = ttk.Button(midIQ, text="Submit", width=10, command=callback)
				b.pack()
				tk.mainloop()
	else: # I.e. if the selection is "None"
		midIndicators = "none"
		reloadQueued = True



def addTopIndicator(name): 
	global topIndicator
	global globalCounter

	if name == 'none': 
		topIndicator = 'none'
		globalCounter = 9000
	elif name == 'rsi': 
		rsiQ = tk.Tk()
		rsiQ.iconbitmap("./img/widget.ico")
		rsiQ.wm_title('Set parameter')
		label = ttk.Label(rsiQ, text = "Choose how many periods you want each RSI calculation to consider.")
		label.pack(side="top", fill="x", pady=10, padx=10)

		e = ttk.Entry(rsiQ)
		e.insert(0,14)
		e.pack()
		e.focus_set()

		def callback(): 
			global topIndicator
			global globalCounter

			periods = (e.get())
			group = []
			group.append("rsi")
			group.append(periods) 

			topIndicator = group
			globalCounter = 9000
			print("Set top indicator to:", group)
			rsiQ.destroy()

		b = ttk.Button(rsiQ, text="Submit", width=10, command=callback)
		b.pack()
		tk.mainloop()

	elif name == "macd":
		topIndicator = "macd"
		globalCounter = 9000


def popupmsg(msg): 
	popup = tk.Tk()
	popup.wm_title("!")
	popup.iconbitmap("./img/widget.ico")
	label = ttk.Label(popup, text=msg, font=MID_FONT)
	label.pack(side="top", fill="x", pady=10)
	B1 = ttk.Button(popup, text="OK", command=popup.destroy)
	B1.pack()
	popup.mainloop()

def animate(i): 
	global reloadQueued

	if reloadQueued: 
		if not currentTickers == None: 
			plt.clf()
			a1 = plt.subplot2grid((6,4), (0,0), rowspan=5, colspan=4)
			a2 = plt.subplot2grid((6,4), (5,0), rowspan=1, colspan=4, sharex=a1)
			a1.clear() 
			a2.clear()
			if len(currentTickers) == 1: 
				d = DATAHANDLER.get_stock_df(currentTickers[0])
				if midIndicators != "none": 
					sma_ctr = 0
					ema_ctr = 0
					for indicator,value in midIndicators: 
						if indicator == "sma":
							a1.plot_date(d.index, d['Adj Close'].rolling(value).mean(), '--',label="SMA {}".format(value), color=SMA_COLORS[sma_ctr])
							sma_ctr += 1
						elif indicator == "ema": 
							a1.plot_date(d.index, d['Adj Close'].ewm(alpha=value).mean(), '--',label="EMA {}".format(value),color=EMA_COLORS[ema_ctr])
							ema_ctr += 1
					a1.plot_date(d.index, d['Adj Close'],'-', color=MAIN_COLORS[0],label=currentTickers[0])
					a1.legend(bbox_to_anchor=(-0.15, 1.02,1, 0.102), loc='lower left', ncol=2, borderaxespad=0)
					a2.fill_between(d.index, 0,d['Volume'],color=MAIN_COLORS[0])
				else: 
					a1.plot_date(d.index, d['Adj Close'],'-', color=MAIN_COLORS[0])
					a2.fill_between(d.index, 0,d['Volume'],color=MAIN_COLORS[0])
				title = "".join(currentTickers)
				a1.set_title(title)
			else: 
				colorIndex = 0
				plt.clf()
				a1 = plt.subplot2grid((6,4), (0,0), rowspan=5, colspan=4)
				a2 = plt.subplot2grid((6,4), (5,0), rowspan=1, colspan=4, sharex=a1)
				a1.clear() 
				a2.clear()
				vols = []
				for ticker in currentTickers:
					if not colorIndex < len(COLORS): # If we're out of pre-chosen colors, randomize one
						color = ["#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])]
					else:
						color = MAIN_COLORS[colorIndex]
						colorIndex += 1
					d = DATAHANDLER.get_stock_df(ticker)
					a1.plot_date(d.index, d['Adj Close'],'-', linewidth=0.5, label=ticker,color=color)
					vols.append(d['Volume'])
				vols = np.asarray(vols)
				a2.fill_between(d.index, 0,vols.sum(axis=0), label=ticker, color="black")
				a1.legend(bbox_to_anchor=(0, 1.02,1, 0.102), loc=3, ncol=2, borderaxespad=0)
			a1.xaxis.set_major_locator(mticker.MaxNLocator(5))
			a1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
			a1.yaxis.tick_right()
			a2.set_title('VOLUME', rotation=90,x=-0.02, y=0, fontsize=8)
			a2.yaxis.set_ticks([])
			plt.xticks(rotation=20)
			plt.setp(a1.get_xticklabels(), visible=False)
			plt.setp(a2.get_yticklabels(), visible=False)
			reloadQueued = False




class DataHandler(): 
	def __init__(self): 
		# Make sure there are tickers
		# self.ticker_path = Path(os.getcwd()) / "data/sap100tickers.pickle"
		self.ticker_path = Path(os.getcwd()) / "data/dummy_tickers.pickle" # DUMMY TICKERS
		self.stock_path = Path(os.getcwd()) / "data/stock_dfs"
		if not self.ticker_path.exists(): 
			self.tickers = self.download_tickers(self.ticker_path)
		else: 
			with open(self.ticker_path, 'rb') as f: 
				self.tickers = pickle.load(f)
		# Check if there is any data at all / new data etc. 
		self.download_all_stocks()


	def download_tickers(self, path):
		resp = requests.get('https://en.wikipedia.org/wiki/S%26P_100')
		soup = bs.BeautifulSoup(resp.text, features='lxml')
		table = soup.find('table', {'class': 'wikitable sortable'})
		tickers = []
		for row in table.findAll('tr')[1:]: 
			ticker = row.findAll('td')[0].text.rstrip()
			if ticker == 'BRK.B': # Hard-coded fix of BRK B-stock. 
				ticker = 'BRK'
			tickers.append(ticker)
		with open(path,'wb') as f: 
			pickle.dump(tickers, f)
		return tickers

	def download_all_stocks(self): 
		if not self.stock_path.exists():
			os.mkdir(self.stock_path)
		for ticker in self.tickers: 
			self.download_single_stock(ticker) 


	def download_single_stock(self, ticker): 
		single_path = Path(os.getcwd()) / "data/stock_dfs/{}.csv".format(ticker)
		if not single_path.exists(): 
			print('Loading {}'.format(ticker))
			try: 
				df = web.DataReader(ticker, 'yahoo', start=startDate, end=endDate)
				df.index = pd.to_datetime(df.index)
				df.to_csv(single_path)
			except KeyError: 
				print("{} not avilable for requested dates.".format(ticker))
			
		else: 
			print('Found {}'.format(ticker))
			df = pd.read_csv(single_path, index_col=0)
			df.index = pd.to_datetime(df.index)
			delta_hours = (endDate - df.index[-1]).seconds / 3600
			if delta_hours > 24: 
			# If the 'end'-time is more than 24 h ahead, remove last index
			# from original df and request df.index[-1] to end from yahoo
				append_start = df.index[-1]
				df.drop(append_start, axis=0, inplace=True)
				append_df = web.DataReader(ticker, 'yahoo', append_start, endDate)
				df = df.append(append_df)
				df.index = pd.to_datetime(df.index)
				df.to_csv(single_path)
			elif delta_hours > 0: 
				# If 'end'-time is less than 24h ahead, do the same but convert to date
				try: 
					append_df = web.DataReader(ticker, 'yahoo', endDate.date(), endDate.date())
					df.drop(df.index[-1], axis=0, inplace=True)
					df = df.append(append_df)
					df.index = pd.to_datetime(df.index)
					df.to_csv(single_path)
				except KeyError: 	
					print("Didn't find new data for {}.".format(ticker))

	def get_stock_df(self, ticker): 
		path = self.stock_path / "".join([ticker, ".csv"])
		if not path.exists(): 
			self.download_single_stock(ticker)
		df = pd.read_csv(path, index_col=0)
		df.index = pd.to_datetime(df.index)
		return df[startDate : endDate]

	def get_all_tickers(self): 
		return self.tickers


class AnalyticGUI(tk.Tk):

	def __init__(self, *args, **kwargs): 
		tk.Tk.__init__(self,*args,**kwargs)
		global DATAHANDLER
		
		DATAHANDLER = DataHandler()
		self.iconbitmap("./img/widget.ico")
		self.wm_title("A-kassa Analytics")
		self.wm_protocol("WM_DELETE_WINDOW", self.exit_routine)

		container = tk.Frame(self)

		container.pack(side='top',fill='both',expand=True)
		
		container.grid_rowconfigure(0, weight=1)
		container.grid_columnconfigure(0, weight=1)

		menubar = tk.Menu(container)
		filemenu = tk.Menu(menubar, tearoff=0)
		filemenu.add_command(label="Save Settings", command= lambda: popupmsg("To be added!"))
		filemenu.add_separator()
		filemenu.add_command(label="Exit", command=self.exit_routine)
		menubar.add_cascade(label="File", menu=filemenu)


		dataTF = tk.Menu(menubar, tearoff=0)
		dataTF.add_command(label="1 week", command=lambda: changeTimeFrame('7d'))
		dataTF.add_command(label="1 month", command=lambda: changeTimeFrame('1m'))
		dataTF.add_command(label="6 months", command=lambda: changeTimeFrame('6m'))
		dataTF.add_command(label="1 year", command=lambda: changeTimeFrame('1y'))
		dataTF.add_command(label="3 years", command=lambda: changeTimeFrame('3y'))
		dataTF.add_command(label="Max", command=lambda: changeTimeFrame('max'))

		menubar.add_cascade(label="Time Frame", menu=dataTF)

		topIndi = tk.Menu(menubar, tearoff=0)
		topIndi.add_command(label="None", command=lambda: addTopIndicator('none'))
		topIndi.add_command(label="RSI", command=lambda: addTopIndicator('rsi'))
		topIndi.add_command(label="MACD", command=lambda: addTopIndicator('macd'))

		menubar.add_cascade(label="Top Indicators", menu=topIndi)

		midIndi = tk.Menu(menubar, tearoff=0)
		midIndi.add_command(label="None", command=lambda: addMidIndicators('none'))
		midIndi.add_command(label="Simple Moving Average", command=lambda: addMidIndicators('sma'))
		midIndi.add_command(label="Exponential Moving Average", command=lambda: addMidIndicators('ema'))

		menubar.add_cascade(label="Mid Indicators", menu=midIndi)

		bottomIndi = tk.Menu(menubar, tearoff=0)
		bottomIndi.add_command(label="None", command=lambda: addBottomIndicator('none'))
		bottomIndi.add_command(label="RSI", command=lambda: addBottomIndicator('rsi'))
		bottomIndi.add_command(label="MACD", command=lambda: addBottomIndicator('macd'))

		menubar.add_cascade(label="Bottom Indicators", menu=topIndi)


		tk.Tk.config(self, menu=menubar)

		self.frames = {}

		for F in [StartPage, HomePage, PageTwo, DashboardPage]: 

			frame = F(container, self) 
			self.frames[F] = frame
			frame.grid(row=0,column=0,sticky="nsew")

		# self.show_frame(StartPage)
		self.show_frame(DashboardPage)	# Just for development
		self.geometry("900x600+200+40")


	def show_frame(self, cont): 
		frame = self.frames[cont]
		frame.tkraise()

	def exit_routine(self): 
		plt.close() 
		self.destroy()



class StartPage(tk.Frame):

	def __init__(self, parent, controller): 
		tk.Frame.__init__(self,parent)
		
		label_large = tk.Label(self, text='A-kassa Analyticas Alpha Release', font=LARGE_FONT) 
		label_large.pack(pady=10, padx=10)
		label_small = tk.Label(self, text="""There is neither safety nor guaranteed profits included in this software. \n Please contact https://www.kommunalsakassa.se for such endeavors.""", font=MID_FONT) 
		label_small.pack(pady=10, padx=10)

		agree_button = ttk.Button(self, text='Agree', command=lambda: controller.show_frame(DashboardPage))
		agree_button.pack()
		disagree_button = ttk.Button(self, text='Disagree', command=controller.exit_routine)
		disagree_button.pack()



class HomePage(tk.Frame): 
	def __init__(self, parent, controller):

		tk.Frame.__init__(self,parent)
		label = ttk.Label(self, text='Home Page', font=LARGE_FONT)
		label.pack(pady=10, padx=10)

		button = ttk.Button(self, text= 'Graph', command=lambda: controller.show_frame(DashboardPage))
		button.pack() 

class PageTwo(tk.Frame): 
	def __init__(self, parent, controller):
		tk.Frame.__init__(self,parent)
		label = tk.Label(self, text='Page Two', font=LARGE_FONT)
		label.pack(pady=10, padx=10)

		button1 = ttk.Button(self, text= 'Start page', command=lambda: controller.show_frame(StartPage))
		button1.pack() 

		button2 = ttk.Button(self, text= 'Page one', command=lambda: controller.show_frame(PageOne))
		button2.pack() 

class DashboardPage(tk.Frame): 
	def __init__(self, parent, controller):
		tk.Frame.__init__(self,parent)

		label = tk.Label(self, text='Dashboard', font=LARGE_FONT)
		label.pack(side="top", pady=2, padx=10)

		widgetBox = tk.Frame(self)

		listbox = tk.Listbox(widgetBox, height=10, width=30)
		listbox.grid(row=0, column=0, columnspan=3, sticky="n")

		[listbox.insert(i,ticker) for i,ticker in enumerate(DATAHANDLER.get_all_tickers())]

		def plot_single(): 
			global currentTickers
			global reloadQueued
			try: 
				sel = listbox.get(listbox.curselection())
				currentTickers = []
				currentTickers.append(sel)
				reloadQueued = True
			except Exception as e: 
				pass

		def plot_several(): 
			global currentTickers
			global reloadQueued
			
			try: 
				sel = listbox.get(listbox.curselection())
				if sel not in currentTickers:
					currentTickers.append(sel)
					reloadQueued = True
			except Exception as e: 
				pass

		plotButton = ttk.Button(widgetBox, text="Plot", command=plot_single)
		plotButton.grid(row=1, column=0, sticky="n")

		addPlotButton = ttk.Button(widgetBox, text="Add to Plot", command=plot_several)
		addPlotButton.grid(row=1, column=1, sticky="n")

		homebutton = ttk.Button(widgetBox, text= 'Home', command=lambda: controller.show_frame(HomePage))
		homebutton.grid(row=3, column=2, sticky="s")		

		widgetBox.pack(side="left", fill="both", expand=True)

		canvas = FigureCanvasTkAgg(f, self)
		canvas.draw() 
		canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

		# For a navigation bar
		toolbar = NavigationToolbar2Tk(canvas, self)
		toolbar.update()
		canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

		reloadQueued = True
		


		
# dummy_tickers = ['AAPL', 'GOOGL', 'C']

# with open("data/dummy_tickers.pickle",'wb') as f1: 
# 	pickle.dump(dummy_tickers, f1)

# with open("data/dummy_tickers.pickle",'rb') as f: 
# 	a = pickle.load(f)
# print(a)


app = AnalyticGUI()
ani = animation.FuncAnimation(f, animate, interval=500)
app.mainloop()
