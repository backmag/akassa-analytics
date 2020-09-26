import tkinter as tk 
from tkinter import ttk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style
style.use("ggplot")

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
MID_FONT = ("Avenir", 8)
CURRENT_TICKER = "AAPL"



f = Figure(figsize=(5,5), dpi=100)
a = f.add_subplot(111)

def animate(i): 
	pullData = open("sampleData.txt", 'r').read()
	dataList = pullData.split('\n')
	xList = []
	yList = []
	for eachLine in dataList: 
		if len(eachLine) > 1: 
			x, y = eachLine.split(',')
			xList.append(int(x))
			yList.append(int(y))
	a.clear()
	a.plot(xList, yList)

class DataHandler(): 

	def __init__(self, start, end): 
		# Make sure there are tickers
		self.ticker_path = Path(os.getcwd()) / "data/sap100tickers.pickle"
		self.stock_path = Path(os.getcwd()) / "data/stock_dfs"
		self.start = start
		self.end = end
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
				df = web.DataReader(ticker, 'yahoo', start=self.start, end=self.end)
				df.index = pd.to_datetime(df.index)
				df.to_csv(single_path)
			except KeyError: 
				print("{} not avilable for requested dates.".format(ticker))
			
		else: 
			print('Found {}'.format(ticker))
			df = pd.read_csv(single_path, index_col=0)
			df.index = pd.to_datetime(df.index)
			delta_hours = (self.end - df.index[-1]).seconds / 3600
			if delta_hours > 24: 
			# If the 'end'-time is more than 24 h ahead, remove last index
			# from original df and request df.index[-1] to end from yahoo
				append_start = df.index[-1]
				df.drop(append_start, axis=0, inplace=True)
				append_df = web.DataReader(ticker, 'yahoo', append_start, self.end)
				df = df.append(append_df)
				df.index = pd.to_datetime(df.index)
				df.to_csv(single_path)
				return df
			elif delta_hours > 0: 
				# If 'end'-time is less than 24h ahead, do the same but convert to date
				try: 
					append_df = web.DataReader(ticker, 'yahoo', self.end.date(), self.end.date())
				except KeyError: 	
					print("Didn't find new date.")
				df.drop(df.index[-1], axis=0, inplace=True)
				df = df.append(append_df)
				df.index = pd.to_datetime(df.index)
				df.to_csv(single_path)

	def get_stock_df(self, ticker): 
		path = self.stock_path / "".join([ticker, ".csv"])
		if not path.exists(): 
			self.download_single_stock(ticker)
		df = pd.read_csv(path, index_col=0)
		df.index = pd.to_datetime(df.index)
		return df


class AnalyticGUI(tk.Tk):

	def __init__(self, datahandler ,*args, **kwargs): 
		tk.Tk.__init__(self,*args,**kwargs)

		self.datahandler = datahandler
		tk.Tk.iconbitmap(self, default="./img/widget.ico")
		tk.Tk.wm_title(self, "A-kassa Analytics")

		container = tk.Frame(self)

		container.pack(side='top',fill='both',expand=True)
		
		container.grid_rowconfigure(0, weight=1)
		container.grid_columnconfigure(0, weight=1)

		self.frames = {}

		for F in [StartPage, HomePage, PageTwo, PageThree]: 

			frame = F(container, self) 
			self.frames[F] = frame
			frame.grid(row=0,column=0,sticky="nsew")

		self.show_frame(StartPage)

	def show_frame(self, cont): 
		frame = self.frames[cont]
		frame.tkraise()


class StartPage(tk.Frame):

	def __init__(self, parent, controller): 
		tk.Frame.__init__(self,parent)
		
		label_large = tk.Label(self, text='A-kassa Analyticas Alpha Release', font=LARGE_FONT) 
		label_large.pack(pady=10, padx=10)
		label_small = tk.Label(self, text="""There is neither safety nor guaranteed profits included in this software. \n Please contact https://www.kommunalsakassa.se for such endeavors.""", font=MID_FONT) 
		label_small.pack(pady=10, padx=10)

		agree_button = ttk.Button(self, text='Agree', command=lambda: controller.show_frame(HomePage))
		agree_button.pack()
		disagree_button = ttk.Button(self, text='Disagree', command=controller.destroy)
		disagree_button.pack()



class HomePage(tk.Frame): 
	def __init__(self, parent, controller):
		tk.Frame.__init__(self,parent)
		label = ttk.Label(self, text='Home Page', font=LARGE_FONT)
		label.pack(pady=10, padx=10)

		button = ttk.Button(self, text= 'Graph', command=lambda: controller.show_frame(PageThree))
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

class PageThree(tk.Frame): 
	def __init__(self, parent, controller):
		tk.Frame.__init__(self,parent)
		label = tk.Label(self, text='Graph Page', font=LARGE_FONT)
		label.pack(pady=10, padx=10)

		button1 = ttk.Button(self, text= 'Home', command=lambda: controller.show_frame(StartPage))
		button1.pack()

		

		canvas = FigureCanvasTkAgg(f, self)
		canvas.draw() 
		canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

		# For a navigation bar
		toolbar = NavigationToolbar2Tk(canvas, self)
		toolbar.update()
		canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

		d = controller.datahandler.get_stock_df(CURRENT_TICKER)['Adj Close']
		a.plot(d)

		





start = datetime(2000,1,1)
end = datetime(2010,1,1)
dh = DataHandler(start,end) 
app = AnalyticGUI(dh)
ani = animation.FuncAnimation(f, animate, interval=1000)
app.mainloop()