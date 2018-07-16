"""
Added to GitHub on Tuesday, Aug 1st 2017

author: Tansel Baran Yasar

Contains the source code for the custom GUI which is aimed to be complementary to the Klustaviewa GUI.
"""

import pyqtgraph as pg
from pyqtgraph.Qt import QtCorec
#from pyqtgraph.Qt import QtCore
import QtGui
#from PyQt4 import QtGui
#from PyQt5 import QtGui
import pyqtgraph.console
import numpy as np
from custom_feature_plots import *
from pyqtgraph.Point import Point
from pyqtgraph.dockarea import *
from pyqtgraph.widgets.MatplotlibWidget import *
from heatmap_plot import *
import pickle
import sys

def calculate_params(waveforms):
    """
    This function takes the waveforms array calculate the custom defined features.

    Inputs:

      waveforms: Array (NxLxM, where N is the number of
    the spiking events detected by the tetrode [or (total number of waveforms/4]
    M is the number of samples per each waveform and L corresponds to the number
    of channels in the tetrode/shank.

    Outputs:

      params: A dictionary with the following parameters:
        peaks: Array consisting of the maximums of the waveforms
        valleys: Array consisting of the minimums of the waveforms
        amps: Peak to peak amplitudes of the waveforms
        widths: Half widths of the waveforms
        integrals: Integrals of the absolute values of the waveforms
    """

    peaks = np.amax(waveforms,2)
    valleys = np.amin(waveforms,2)
    amps = peaks - valleys
    begin = np.zeros((len(waveforms), len(waveforms[0])))
    end = np.zeros((len(waveforms), len(waveforms[0])))

    for i in range(len(waveforms)):
        for j in range(len(waveforms[0])):
            began = False
            for k in range(len(waveforms[0][0])):
                if (waveforms[i][j][k] > (valleys[i][j] + amps[i][j] / 2)):
                    if began:
                        end[i][j] = k
                        began = False
                    else:
                        begin[i][j] = k
                        began = True

    energy = np.square(waveforms)
    energy = np.sum(energy, 2)
    energy = np.sqrt(energy)

    widths = end - begin

    params = {'peaks': peaks, 'valleys':valleys, 'Amplitude':amps, 'widths':widths, 'Energy': energy}

    return params

def generate_scatter_plot(params_dict, feature1, electrode1, feature2, electrode2):
    """
    This function takes the parameters calculated for the waveforms and generates a scatter plot for
    selected electrodes and features.

    Inputs:

      params_dict: Dictionary containing the waveform parameters as generated by the calculate_params
        function.
      feature1: The feature to be plotted on x axis.
      electrode1: From which electrode the parameter will be pulled for the x axis.
      feature2: The feature to be plotted on y axis.
      electrode2: From which electrode the parameter will be pulled for the y axis.

    Outputs:
      plt: Scatter plot item containing the scatter plot generated for the selected parameters
    """

    y_label = feature2+' on Electrode #'+str(electrode2)
    x_label = feature1+' on Electrode #'+str(electrode1)
    plt = pg.PlotItem(labels={'left': y_label, 'bottom': x_label})
    s = pg.ScatterPlotItem()
    spots = []

    for i in range(n_clusters):
        feat1_array = params_dict[str(i)][feature1]
        feat2_array = params_dict[str(i)][feature2]
        pos = np.column_stack((feat1_array[:,electrode1], feat2_array[:,electrode2]))
        for j in range(len(feat1_array)):
            spots.append({'pos': pos[j,:], 'size':5, 'symbol': 'o', 'pen': pg.mkPen(None), 'brush': pg.intColor(i,n_clusters)})
    s.addPoints(spots)
    plt.addItem(s)
    return plt

def generate_datascope(raw_data, interval):
    """
    This function plots a specified interval of the raw data on the Tetrodescope.

    Inputs:
      raw_data: LxN array consisting of the raw data from the electrodes where N
            is the number of samples in each electrode and L is the number of electrodes
            in the tetrode/shank.
      interval: Interval defined by the user over which the data will be plotted in
            datascope.

    Outputs:
      plt: Plot item containing the plot of the raw tetrode data over the interval.
    """
    x_label = 'Time (s)'
    y_label = 'Voltage scale bar (uV)'
    windowmin = interval[0] * p['sample_rate']
    windowmax = interval[1] * p['sample_rate']
    time = np.linspace(interval[0], interval[1], (windowmax-windowmin))

    plt = pg.PlotItem(labels={'left':y_label, 'bottom':x_label})
    for electrode in range(4):
        plt.plot(time,raw_data[electrode,windowmin:windowmax] + 100*electrode)

    for clu in range(n_clusters):
        pen1 = pg.mkPen(pg.intColor(clu,n_clusters))

        times = []
        connect = []

        pre = p['samples_before']
        post = p['samples_after']
        for time in spike_info_dict[('c'+str(clu))][0]:
            if (time > windowmin) and (time < windowmax):
                begin = max([(time-pre),0])
                end = min([len(raw_data[0,:]),(time+post)])
                ran = np.r_[begin:end]
                times = np.append(times, ran)
                times = times.astype('int')
                connect_ind = np.ones(len(ran))
                connect_ind[-1] = 0
                connect = np.append(connect, connect_ind)
        times_real = np.divide(times,p['sample_rate'])

        for electrode in range(4):
            plt.plot(times_real, raw_data[electrode,times]+electrode*100, connect=connect, pen=pen1)

    return plt

def createWindow(interval):
    region = pg.LinearRegionItem()
    region.setZValue(100)
    plot_big.addItem(region)

    def update9():
        region.setZValue(100)
        minX, maxX = region.getRegion()
        plot_zoom.setXRange(minX, maxX, padding=0)

    def updateRegion(window, viewRange):
        rgn = viewRange[0]
        region.setRegion(rgn)

    region.sigRegionChanged.connect(update9)
    plot_zoom.sigRangeChanged.connect(updateRegion)
    region.setRegion(interval)

### Call the waveform dictionary and timestamps from pickle file

pickle_file = str(sys.argv[1])
main_dict = pickle.load(open(pickle_file, 'rb'))
spike_info_dict = main_dict['P']
raw_data = main_dict['data']
p = main_dict['p']

n_clusters = len(spike_info_dict)

params_dict = {}
for i in range(n_clusters):
    params_dict[str(i)] = calculate_params(spike_info_dict[('c'+str(i))][2])

### Create the application and main window

app = QtGui.QApplication([])
win = QtGui.QMainWindow()
area = DockArea()
win.setCentralWidget(area)
win.resize(1500,1000)
win.setWindowTitle('Spike Sorting GUI')

### Create docks, place them into the window one at a time.
d1 = Dock("Plot configuration", size=(200,200), closable=True)
d2 = Dock("Waveform Density Heatmap", size=(200,200), closable=True)
d3 = Dock("Scatter Plot 1", size=(400,300), closable=True)
d4 = Dock("Scatter Plot 2", size=(400,300), closable=True)
d5 = Dock("Scatter Plot 3", size=(400,300), closable=True)
d6 = Dock("Scatter Plot 4", size=(400,300), closable=True)
d7 = Dock("Scatter Plot 5", size=(400,300), closable=True)
d8 = Dock("Scatter Plot 6", size=(400,300), closable=True)
d9 = Dock("Tetrodescope", size=(1500,400), closable=True)

area.addDock(d1, 'left')
area.addDock(d2, 'bottom', d1)
area.addDock(d3, 'right', d1)
area.addDock(d4, 'right', d3)
area.addDock(d5, 'right', d4)
area.addDock(d6, 'bottom', d3)
area.addDock(d7, 'bottom', d4)
area.addDock(d8, 'bottom', d5)
area.addDock(d9, 'bottom')

area.moveDock(d2, 'bottom', d1)

### Add widgets into each dock

## First dock for scatter plot configuration

#Divide the first dock into different sections

w1 = pg.LayoutWidget()

layout1 = w1.addLayout(row=1,col=1,rowspan=1,colspan=2)
layout2 = w1.addLayout(2,1,1,1)
layout3 = w1.addLayout(2,2,1,1)
layout4 = w1.addLayout(3,1,1,1)
layout5 = w1.addLayout(3,2,1,1)
layout6_1 = w1.addLayout(4,1,2,1)
layout6_2 = w1.addLayout(4,2,2,1)
#layout7 = w1.addLayout(5,1,1,2)

#First section of the first dock is for intro text, selection of the scatter plot dock to be updated and the update button

text_intro = QtGui.QLabel('Welcome to the Spike Sorting GUI. For updating the scatter plots, first select a dock to be updated \n \
    (from 1 to 6), then select with respect to which featurres from which electrodes you would like \n to generate the scatter plots. \
    Once you have selected the dock, electrodes and features press Update \n to update the scatter plot.')

spin_dock = pg.SpinBox(value=1, bounds=(1,6), int=True, step=1)
updateScatterBtn = QtGui.QPushButton('Update')

tree1 = pg.TreeWidget()
feat1_1 = QtGui.QTreeWidgetItem(["Amplitude"])
feat1_2 = QtGui.QTreeWidgetItem(["Energy"])
tree1.addTopLevelItem(feat1_1)
tree1.addTopLevelItem(feat1_2)

tree2 = pg.TreeWidget()
feat2_1 = QtGui.QTreeWidgetItem(["Amplitude"])
feat2_2 = QtGui.QTreeWidgetItem(["Energy"])
tree2.addTopLevelItem(feat2_1)
tree2.addTopLevelItem(feat2_2)

spin_electrode1 = pg.SpinBox(value=0, bounds=(0,3), int=True, step=1)
spin_electrode2 = pg.SpinBox(value=0, bounds=(0,3), int=True, step=1)

num_seconds = int(len(raw_data[0,:])/p['sample_rate'])
spin_windowmin = pg.SpinBox(value=0, bounds=(0, num_seconds), int=True, step=1)
spin_windowmax = pg.SpinBox(value=5, bounds=(0, num_seconds), int=True, step=1)
updateWinBtn = QtGui.QPushButton('Update DataScope')

saveBtn = QtGui.QPushButton('Save dock state')
restoreBtn = QtGui.QPushButton('Restore dock state')

state = None

# Setting the button functions in this dock.

def save():
    global state
    state = area.saveState()
    restoreBtn.setEnabled(True)
def load():
    global state
    area.restoreState(state)

saveBtn.clicked.connect(save)
restoreBtn.clicked.connect(load)
restoreBtn.setEnabled(False)

def updateScatter():
    dock = spin_dock.value()
    x_feature_item = tree1.currentItem()
    y_feature_item = tree2.currentItem()
    x_feature = x_feature_item.text(0)
    y_feature = y_feature_item.text(0)
    x_electrode = spin_electrode1.value()
    y_electrode = spin_electrode2.value()

    x_feature_str = str(x_feature)
    y_feature_str = str(y_feature)

    docks = {'1':w3, '2':w4, '3':w5, '4':w6, '5':w7, '6':w8}
    plt = generate_scatter_plot(params_dict, x_feature_str, x_electrode, y_feature_str, y_electrode)
    docks[str(dock)].clear()
    docks[str(dock)].addItem(plt)

updateScatterBtn.clicked.connect(updateScatter)

def updateWin():
    windowmin = spin_windowmin.value()
    windowmax = spin_windowmax.value()
    if windowmax > windowmin:
        plot_big = generate_datascope(raw_data, [windowmin, windowmax])
        plot_zoom = generate_datascope(raw_data, [windowmin, windowmax])
    plot_window_big.clear()
    plot_window_zoom.clear()
    region = pg.LinearRegionItem()
    region.setZValue(100)
    plot_big.addItem(region)

    def update9():
        region.setZValue(100)
        minX, maxX = region.getRegion()
        plot_zoom.setXRange(minX, maxX, padding=0)

    def updateRegion(window, viewRange):
        rgn = viewRange[0]
        region.setRegion(rgn)

    region.sigRegionChanged.connect(update9)
    plot_zoom.sigRangeChanged.connect(updateRegion)
    region.setRegion([windowmin+1,windowmin+2])

    plot_window_big.addItem(plot_big)
    plot_window_zoom.addItem(plot_zoom)

updateWinBtn.clicked.connect(updateWin)

#Adding the widgets in the sections
layout1.addWidget(text_intro, row=1, col=1, rowspan=1, colspan=1)
layout1.addWidget(spin_dock, row=2, col=1, rowspan=1, colspan=1)
layout1.addWidget(updateScatterBtn, row=2, col=2, rowspan=1, colspan=1)

layout2.addWidget(tree1)
text_sel1 = QtGui.QLabel('Please select the electrode and feature for x axis')
text_sel2 = QtGui.QLabel('Please select the electrode and feature for y axis')
layout3.addWidget(text_sel1, row=1)
layout3.addWidget(spin_electrode1, row=2)

layout4.addWidget(tree2)

layout5.addWidget(text_sel2, row=1)
layout5.addWidget(spin_electrode2, row=2)

text_windowmin = QtGui.QLabel('Beginning of DataScope (s)')
text_windowmax = QtGui.QLabel('End of DataScope (s)')
layout6_1.addWidget(text_windowmin, row=1, col=1)
layout6_1.addWidget(text_windowmax, row=1, col=2)
layout6_1.addWidget(spin_windowmin, row=2, col=1)
layout6_1.addWidget(spin_windowmax, row=2, col=2)

layout6_2.addWidget(updateWinBtn, row=1, col=1, rowspan=1, colspan=1)
#layout7.addWidget(saveBtn, row=1, col=1, rowspan=1, colspan=1)
#layout7.addWidget(restoreBtn, row=1, col=2, rowspan=1, colspan=1)

d1.addWidget(w1)

##Waveform density heatmap plot in the second dock

w2 = pg.LayoutWidget()
layout2_1 = w2.addLayout(row=1,col=1,rowspan=1,colspan=2)
layout2_2 = w2.addLayout(2,1,1,2)
layout2_3 = w2.addLayout(3,1,1,2)

text_heatmap = QtGui.QLabel('Please select an electrode an cluster to generate the waveform density heatmap')

if p['probe_type'] == 'tetrode':
    text_heatmap_electrode = QtGui.QLabel('Electrode (0-3)')
    text_heatmap_cluster = QtGui.QLabel('Cluster')

    spin_heatmap_electrode = pg.SpinBox(value=0, bounds=(0, 3), int=True, step=1)
    spin_heatmap_cluster = pg.SpinBox(value=0, bounds=(0, n_clusters), int=True, step=1)
elif p['probe_type'] == 'linear':
    text_heatmap_electrode = QtGui.QLabel('Electrode (0-{:g})'.format(p['nr_of_electrodes_per_shank']))
    text_heatmap_cluster = QtGui.QLabel('Cluster')

    spin_heatmap_electrode = pg.SpinBox(value=0, bounds=(0,p['nr_of_electrodes_per_shank']), int=True, step=1)
    spin_heatmap_cluster = pg.SpinBox(value=0, bounds=(0, n_clusters), int=True, step=1)

generateHeatmapBtn = QtGui.QPushButton('Generate Heatmap')

def generateHeatmap():
    e = spin_heatmap_electrode.value()
    c = spin_heatmap_cluster.value()
    generate_heatmap_interpolated(c,e,main_dict)

generateHeatmapBtn.clicked.connect(generateHeatmap)

layout2_1.addWidget(text_heatmap, 1,1,1,2)

layout2_2.addWidget(text_heatmap_electrode,row=1,col=1)
layout2_2.addWidget(text_heatmap_cluster,row=1,col=2)
layout2_2.addWidget(spin_heatmap_electrode,row=2,col=1)
layout2_2.addWidget(spin_heatmap_cluster,row=2,col=2)

layout2_3.addWidget(generateHeatmapBtn,row=3,col=1,rowspan=1,colspan=2)

d2.addWidget(w2)

##Scatter Plots in docks 3-8

w3 = pg.GraphicsLayoutWidget()
s3 = generate_scatter_plot(params_dict, 'Amplitude', 0, 'Energy', 0)
w3.addItem(s3)
d3.addWidget(w3)

w4 = pg.GraphicsLayoutWidget()
s4 = generate_scatter_plot(params_dict, 'Amplitude', 1, 'Energy', 1)
w4.addItem(s4)
d4.addWidget(w4)

w5 = pg.GraphicsLayoutWidget()
s5 = generate_scatter_plot(params_dict, 'Amplitude', 2, 'Energy', 2)
w5.addItem(s5)
d5.addWidget(w5)

w6 = pg.GraphicsLayoutWidget()
s6 = generate_scatter_plot(params_dict, 'Amplitude', 3, 'Energy', 3)
w6.addItem(s6)
d6.addWidget(w6)

w7 = pg.GraphicsLayoutWidget()
s7 = generate_scatter_plot(params_dict, 'Amplitude', 0, 'Amplitude', 1)
w7.addItem(s7)
d7.addWidget(w7)

w8 = pg.GraphicsLayoutWidget()
s8 = generate_scatter_plot(params_dict, 'Amplitude', 0, 'Amplitude', 2)
w8.addItem(s8)
d8.addWidget(w8)

##Datascope in dock 9

w9 = pg.LayoutWidget()

layout9_1 = w9.addLayout(row=1,col=1,rowspan=1)
layout9_2 = w9.addLayout(row=1,col=1,rowspan=1)

plot_window_big = pg.GraphicsLayoutWidget()
plot_window_zoom = pg.GraphicsLayoutWidget()

if p['probe_type'] == 'tetrode':
    plot_big = generate_tetrodescope(raw_data, [0,5])
    plot_zoom = generate_tetrodescope(raw_data, [0,5])
elif p['probe_type'] == 'linear':
    plot_big = generate_tetrodescope(raw_data, [0, p['nr_of_electrodes_per_shank']+1])
    plot_zoom = generate_tetrodescope(raw_data, [0, p['nr_of_electrodes_per_shank']+1])

plot_window_big.addItem(plot_big,row=1, col=1, rowspan=1, colspan=1)
plot_window_zoom.addItem(plot_zoom,row=1, col=1, rowspan=1, colspan=1)

layout9_1 = w9.addWidget(plot_window_big)
layout9_2 = w9.addWidget(plot_window_zoom)

createWindow([1,2])

d9.addWidget(w9)

win.show()

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
