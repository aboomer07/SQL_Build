################################################################################
# Main Script to Initiate the Scripts Correctly
################################################################################

import os  # Import for directory definitions
import sys  # Import to make sure scripts can be imported correctly
import pkgutil as pkg  # Get this library for listing current packages

global currDir

################################################################################
# Use the sys.executable to get the correct python version for executable
################################################################################

python = sys.executable

################################################################################
# Forcing the current directory
################################################################################

dirsplit = os.getcwd().split("/")
if 'Code' == dirsplit[-1]:
    currDir = os.path.abspath("/".
                              join(dirsplit[:-1]))
else:
    currDir = os.getcwd()

os.chdir(currDir)

if not os.path.isdir("Output"):
    os.mkdir("Output")

################################################################################
# Make sure that the scripts will look in the code file for script imports
################################################################################

sys.path.append('Code')

################################################################################
# Get the missing libraries needed to run this project
################################################################################

required = {'sqlite3', 'pandas', 'numpy', 're', 'gspread',
            'oauth2client', 'tabulate', 'plotly', 'itertools',
            'matplotlib', 'seaborn', 'pkgutil', 'itertools',
            'geopandas', 'statsmodels', 'Pillow', 'tkinter'}
installed = {i[1] for i in pkg.iter_modules()}

base = {i for i in sys.builtin_module_names}

missing = required - installed - base

################################################################################
# If the set of missing libraries is not empty, then install missing with pip
################################################################################

if missing:
    os.system(" ".join([python, '-m', 'pip', 'install'] + [i for i in missing]))

################################################################################
# Define list of tables and connect to the sqlite database
################################################################################

from DBFill import *
from Queries import *
from tkinter import *
from tabulate import tabulate
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import geopandas
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.ticker as mtick
from PIL import ImageTk, Image
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
import re

tables = ['Action', 'ActionType', 'Applying',
          'Certifying', 'Company', 'Eligibility', 'Funding', 'Improvement',
          'Labelling', 'Supporting', 'ActionFund']

cols = {'Action': ['AID', 'Likes', 'Year', 'CID', 'TID'],
        'ActionFund': ['AID', 'FID', 'AwardYear', 'Amount'],
        'ActionType': ['TID', 'Category', 'Description', 'MainImpact'],
        'Applying': ['AID', 'FID'],
        'Certifying': ['CID', 'TID'],
        'Company': ['CID', 'Name', 'City', 'Country', 'Website', 'Sector', 'Size'],
        'Eligibility': ['FID', 'TID'],
        'Funding': ['FID', 'Name', 'Procedure', 'Cumulative', 'MaxAmount'],
        'Improvement': ['IID', 'Emissions', 'Turnover', 'GreenInvest', 'GreenRecruit', 'CID', 'Year'],
        'Labelling': ['CID', 'AID'],
        'Supporting': ['CID', 'TID']}


################################################################################
# Ask User If They Want to Run Queries Iteratively
################################################################################

class mainWindow(object):
    def __init__(self, master, wsheet, cnxn, tables, cols):
        self.master = master
        self.cnxn = cnxn
        self.tables = tables
        self.cols = cols
        self.wsheet = wsheet

        img = ImageTk.PhotoImage(Image.open("TSE.png"))
        TSE = Label(master, image = img)
        TSE.image = img
        TSE.place(x=0, y=0)

        img = Image.open("SQLITE.png")
        img = img.resize((200, 125), Image.ANTIALIAS)
        img = ImageTk.PhotoImage(img)
        sq_lite = Label(master, image=img)
        sq_lite.image = img
        sq_lite.pack(anchor='ne')

        self.Bar = Canvas(root, width=500, height=125)
        self.Bar.place(x=335, y=0)
        self.Bar.create_rectangle(0, 0, 500, 125, fill='grey')

        title = Label(master, justify=CENTER, 
              text='Databases Project', bg='grey')
        title.config(font=("Courier", 25))
        title.place(x=450, y=10)

        by = Label(master, justify=CENTER, 
              text='by', bg='grey')
        by.config(font=("Courier", 15))
        by.place(x=575, y=50)

        authors = Label(master, justify=CENTER, 
              text='Andrew Boomer & Jacob Pichelmann', bg='grey')
        authors.config(font=("Courier", 20))
        authors.place(x=400, y=75)

        self.Exit = Button(master, text='Exit App',
                           command=lambda: self.Leave())
        self.Exit.place(x=0, y=150)

        self.FillDB = Button(master, text='Fill Database',
                             command=lambda: self.Fill())
        self.FillDB.place(x=100, y=150)

        self.output = Text(master)
        self.output.place(x=50, y=200, height=500, width=890)

        # self.qs = [key for key in q_dict.keys() if key in ['Open', 'R12', 'R9']]
        self.qs = [key for key in q_dict.keys()]
        self.q = 0
        self.company = ""

        self.Package = Text(master)
        self.Package.place(x=700, y=130, height=25, width=300)

    def Fill(self):
        self.FillDB.destroy()
        insert_str = fill_db(self.wsheet, self.cnxn, self.tables)
        self.output.insert("end-1c", insert_str)
        with open("Output/LatexDBFill.tex", 'w') as f:
             f.write(insert_str)

        self.cont = Button(self.master, text='Next Query',
                           command=lambda: self.Continue())
        self.cont.place(x=100, y=150)

    def ToLatex(self):
        try:
            self.toTex.destroy()
        except:
            pass
        self.cont.destroy()

        out_string = self.header
        out_string = out_string.replace("-\n", "-\n\\\\")
        out_string = out_string.replace("\n-", "\\\\\n-")
        out_string += self.q_string
        res = re.findall("(?<=)SELECT[\s\S]+[^-](?=-)", out_string)[0]
        out_string = out_string.replace(res, "\\begin{lstlisting}[language = SQL]\n" + res + "\\end{lstlisting}\n") + "\\\\"
        out_string += tabulate(self.res_data,
                            headers=self.col_dict[self.Qu],
                            tablefmt='latex_booktabs')
        
        with open('Output/Latex_' + self.Qu + '.tex', 'w') as f:
            f.write(out_string)

        self.output.delete(1.0, 'end-1c')
        if self.q == len(self.qs):
            self.master.destroy()
        self.Iterate(include_tex=False)

    def Continue(self):
        if self.q == len(self.qs):
            self.master.destroy()
        try:
            self.toTex.destroy()
        except:
            pass

        try:
            self.PlotButton.destroy()
            self.embed_fig.destroy()
            self.toolbar.destroy()
        except:
            pass

        self.cont.destroy()
        self.output.delete(1.0, "end-1c")
        self.Package.delete(1.0, "end-1c")

        sql_dict, self.col_dict = get_sql(self.cnxn)
        self.Qu = self.qs[self.q]
        self.header = "-" * 80 + '\n' + q_dict[self.Qu]
        self.header += '\n' + "-" * 80
        self.query = sql_dict[self.Qu]

        if self.Qu == 'R9':

            self.top = Toplevel(self.master)
            self.myLabel = Label(self.top, text='Choose Company')
            self.myLabel.pack()
            get_comp = 'SELECT DISTINCT NAME FROM COMPANY'
            companies = self.cnxn.execute(get_comp).fetchall()
            companies = [i[0] for i in companies]
            variable = StringVar(self.master)
            variable.set(companies[0]) # default value

            self.dropdown = OptionMenu(self.top, variable, *companies)
            self.dropdown.pack()

            self.mySubmitButton = Button(self.top,
                text='Submit', command=lambda: self.top_end(variable))
            self.mySubmitButton.pack()
            return(None)

        if self.Qu in ['F1', 'R1']:

            self.top = Toplevel(self.master)
            self.myLabel = Label(self.top, text='Choose Sector')
            self.myLabel.pack()
            get_comp = 'SELECT DISTINCT SECTOR FROM COMPANY'
            companies = self.cnxn.execute(get_comp).fetchall()
            companies = [i[0] for i in companies]
            variable = StringVar(self.master)
            variable.set(companies[0]) # default value

            self.dropdown = OptionMenu(self.top, variable, *companies)
            self.dropdown.pack()

            self.mySubmitButton = Button(self.top,
                text='Submit', command=lambda: self.top_end(variable))
            self.mySubmitButton.pack()
            return(None)

        if self.Qu == 'F1.5':
            self.top_end(self.F1)
            return(None)

        self.q_string = self.query + '\n' + '-' * 80 + '\n'

        self.output.insert('end-1c', self.header)
        self.output.insert('end-1c', self.q_string)

        self.Package.insert('end-1c', "Currently Running " + pkg_dict[self.Qu])

        self.Exec = Button(self.master, text='Run Query',
                           command=lambda: self.Exec_Q())
        self.Exec.place(x=200, y=150)

    def Exec_Q(self):
        if self.q == len(self.qs):
            self.master.destroy()
        self.Exec.destroy()
        if self.Qu in ['R2', 'R4', 'R9', 'R12', 'Open']:
            self.PlotButton = Button(self.master, text='Generate Plot',
                                     command=lambda: self.mkPlot())
            self.PlotButton.place(x=400, y=150)

        if self.Qu != 'Open':
            self.res = self.cnxn.execute(self.query)
            self.res_data = self.res.fetchall()
        else:
            self.res_data = action_pred(self.cnxn)

        res_tab = tabulate(self.res_data,
            headers=self.col_dict[self.Qu],
            tablefmt='fancy_grid')

        if self.Qu in ['F1', 'F2']:
            self.output.insert('end-1c', "\n" + 'View has been successfully created!')
        else:
            self.output.insert('end-1c', "\n" + res_tab)
        self.q += 1

        self.Iterate()

    def Iterate(self, include_tex=True):
        self.cont = Button(self.master, text='Next Query',
                           command=lambda: self.Continue())
        self.cont.place(x=100, y=150)
        if include_tex:
            self.toTex = Button(self.master, text='Write Latex',
                                command=lambda: self.ToLatex())
            self.toTex.place(x=300, y=150)

    def mkPlot(self):
        self.PlotButton.destroy()
        if self.Qu == 'R2':
            self.plotdata = pd.DataFrame(self.res_data, columns=['Sector', 'GrantedActions', 'TotalAmount'])
            fig, ax = plt.subplots(ncols=1, nrows=1)
            fig.suptitle("Funded Actions, Count/Amount")

            f = sns.barplot(data=self.plotdata, x='Sector', y='GrantedActions', ax=ax)
            values = list(self.plotdata['TotalAmount'])
            rects = ax.patches
            for rect, value in zip(rects, values):
                height = rect.get_height()
                ax.text(rect.get_x() + rect.get_width() / 2, height + 0.01, str(round(value)),
                        ha='center', va='bottom')

            self.Embed(fig)
            plt.savefig(os.getcwd() + '/Output/R2_plot')

        elif self.Qu == 'R4':
            self.plotdata = pd.DataFrame(self.res_data, columns=['Country', 'NumCompanies'])
            world = geopandas.read_file(geopandas.datasets.get_path('naturalearth_lowres'))
            world.columns = ['pop_est', 'continent',
                             'name', 'CODE', 'gdp_md_est', 'geometry']
            self.mapdata = pd.merge(world, self.plotdata,
                                    left_on='name', right_on='Country', how='left')

            self.mapdata['coords'] = self.mapdata['geometry'].apply(
                lambda x: x.representative_point().coords[:])
            self.mapdata['coords'] = [coords[0] for coords in self.mapdata['coords']]

            fig, ax = plt.subplots(1, 1)
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("bottom", size="3%", pad=0.1)
            self.mapdata.plot(column='NumCompanies', legend=True, cmap='Blues',
                legend_kwds={'label': "Number of Firms",
                                           'orientation': "horizontal"}, ax=ax, cax=cax,
                              missing_kwds=dict(color="lightgrey"))
            ax.set_axis_off()

            plt.savefig(os.getcwd() + '/Output/R4_plot')
            self.Embed(fig)

        elif self.Qu == 'R9':
            self.plotdata = pd.DataFrame(self.res_data, 
                columns=['CID', 'Name', 'Year', 'GreenRecruit', 'GreenInvest',
                    'Turnover', 'GreenInvestPercentage'])

            fig, axes = plt.subplots(nrows=2, ncols=1)

            sns.lineplot(data=self.plotdata, x='Year', y='GreenRecruit',
                         hue='Name', ax=axes[0])
            axes[0].set_title("Number of Green Recruitments")
            axes[0].legend(bbox_to_anchor=(1.05, 1), borderaxespad=0., title='Company')
            axes[0].get_legend().remove()

            sns.lineplot(data=self.plotdata, x='Year', y='GreenInvestPercentage',
                         hue='Name', ax=axes[1])
            years = [int(i) for i in self.plotdata['Year'].unique()]
            ticks = [i for i in axes[0].get_xticks() if i in years]
            axes[0].set_xticks(ticks)
            axes[0].set_xticklabels(years)

            axes[1].set_title("Percentage of Green Investments to Total Turnover")
            axes[1].legend(bbox_to_anchor=(1.05, 1), borderaxespad=0., title='Company')
            axes[1].yaxis.set_major_formatter(mtick.PercentFormatter(100))
            axes[1].get_legend().remove()

            handles, labels = axes[0].get_legend_handles_labels()
            fig.legend(handles, labels, loc='upper right', ncol=3)

            ticks = [i for i in axes[1].get_xticks() if i in years]
            axes[1].set_xticks(ticks)
            axes[1].set_xticklabels(years)

            plt.tight_layout()
            plt.savefig(os.getcwd() + '/Output/R9_plot')
            self.Embed(fig)

        elif self.Qu == 'R12':
            self.plotdata = pd.DataFrame(self.res_data,
                                         columns=['AwardYear', 'YearlyAmt'])

            fig, ax = plt.subplots(nrows=1, ncols=1)

            sns.lineplot(data=self.plotdata, x='AwardYear', y='YearlyAmt')
            ax.set_title("Evolution of Total Funding Amount")

            years = [int(i) for i in self.plotdata['AwardYear'].unique()]
            ticks = [i for i in ax.get_xticks() if i in years]
            plt.xticks(ticks, years)

            plt.savefig(os.getcwd() + '/Output/R12_plot')
            self.Embed(fig)

        elif self.Qu == 'Open':
            self.plotdata = pd.DataFrame(self.res_data,
                                         columns=['Year', 'NumActions'])

            fig, ax = plt.subplots(nrows=1, ncols=1)
            fig.suptitle('Open Question Forecast')
            ax.set_ylabel("Number of Yearly Actions")

            years = [int(i) for i in self.plotdata['Year'].unique()]

            self.plotdata[self.plotdata['Year'] < 2021]\
                .plot(x='Year', y='NumActions',
                ls="-", color="b", ax=ax, label='True')

            self.plotdata[self.plotdata['Year'] >= 2020].\
                plot(x='Year', y='NumActions',
                ls="--", color="r", ax=ax, label='Forecast')

            ticks = [i for i in ax.get_xticks() if i in years]
            plt.xticks(ticks, years)

            plt.savefig(os.getcwd() + '/Output/Open_plot')
            self.Embed(fig)

        else:
            pass
        
    def top_end(self, variable):
        if self.Qu == 'F1':
            self.top.destroy()
            self.query = "\nCREATE VIEW ActionsIn" + variable.get() + " AS " + self.query
            self.query += "\nAND COMPANY.SECTOR = '" + variable.get() + "'"
            self.q_string = self.query + '\n' + '-' * 80
            self.F1 = variable.get()

        if self.Qu == 'F1.5':
            self.top.destroy()
            self.query += "ActionsIn" + self.F1
            self.q_string = self.query + '\n' + '-' * 80

        if self.Qu == 'R1':
            self.top.destroy()
            self.query += "\nAND COMPANY.SECTOR = '" + variable.get() + "'"
            self.q_string = self.query + '\n' + '-' * 80

        if self.Qu == 'R9':
            self.top.destroy()
            self.query += "\nAND COMPANY.NAME = '" + variable.get() + "'"
            self.q_string = self.query + '\n' + '-' * 80

        self.output.insert('end-1c', self.header)
        self.output.insert('end-1c', self.q_string)
        self.Package.insert('end-1c', "Currently Running " + pkg_dict[self.Qu])

        self.Exec = Button(self.master, text='Run Query',
                               command=lambda: self.Exec_Q())
        self.Exec.place(x=200, y=150)

    def Leave(self):
        self.master.destroy()

    def Embed(self, fig):
        canvas = FigureCanvasTkAgg(fig, master=self.master)
        canvas.draw()
        self.embed_fig = canvas.get_tk_widget()
        self.embed_fig.place(x=50, y=200, height=500, width=890)

        self.toolbar = NavigationToolbar2Tk(canvas, self.master)
        self.toolbar.update()
        canvas.get_tk_widget().place(x=50, y=200, height=500, width=890)

root = Tk()
root.geometry("1000x750")
root.title("Select Run Type")
m = mainWindow(root, wsheet, cnxn, tables, cols)
root.mainloop()
