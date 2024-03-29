#===============================================================================
# Title of this Module
# Authors; MJones, Other
# 00 - 2012FEB05 - First commit
# 01 - 2012MAR17 - Update to ...
#===============================================================================

"""This module does A and B.
Etc.
"""

#--- SETUP Config
from __future__ import division
import logging.config
from config.config import *
myLogger = logging.getLogger()
myLogger.setLevel("DEBUG")

#import sys 
#print('\n'.join(sys.path))

#--- SETUP Standard modules
#import unittest
#import itertools
#import collections
#from collections import defaultdict
import re
import shutil
from pprint import pprint


#--- SETUP 3rd party modules
import pandas as pd
#import xlwt
#import xlrd
#import pandas as pd
#from pprint import pprint
#import exergy_frame as xrg
import numpy as np
import lxml.html
from xml.etree.ElementTree import tostring
#pp = pprint.PrettyPrinter(indent=4)
from openpyxl import load_workbook


#--- SETUP Custom modules
#from utility_inspect import get_self, get_parent
#from exergy_frames import exergy_frame as xrg
#from exergyframes import exergy_frame2 as xrg2
#from exergy_frame import exergy_frame as xrg


#--- SETUP Utilities
from ExergyUtilities.utility_inspect import get_self, get_parent, list_object
from ExergyUtilities.utility_path import filter_files_dir
#from utility_GUI import simpleYesNo
#from utility_path import filter_files_dir,get_latest_rev
#from utility_XML import printXML
import ExergyUtilities.utility_path as util_paths
from ExergyUtilities.utility_excel_api import ExtendedExcelBookAPI
from ExergyUtilities.util_pretty_print import print_table


TABLES =[
         {'section'     :   'Annual Building Utility Performance Summary',  'table' :   'Site and Source Energy'  },
         {'section'      :  'Input Verification and Results Summary',       'table' :  'General'},
         {'section'      :  'LEED Summary',                                 'table' :      'EAp2-4/5. Performance Rating Method Compliance'},
         {'section'      :  'Annual Building Utility Performance Summary',  'table' :  'Building Area'                           },
         {'section'      :  'Annual Building Utility Performance Summary',  'table' :  'End Uses'},
         {'section'      :  'Annual Building Utility Performance Summary',  'table' :  'Comfort and Setpoint Not Met Summary'},
         {'section'      :  'Input Verification and Results Summary',       'table' :  'Window-Wall Ratio'},
         #{'section'      :                  'Sensible Heat Gain Summary',               'table'         :  'Window-Wall Ratio'                        },
          ]


#--- Utility
def massConvertGJ_kWh(frame):
    # CONVERSION
    def convertGJ_kWh(item):
        if not item:
            item = "0"
        try:
            newItem = float(item) * 277.7
        except:
            if item:
                print("YES")
            print(item)
            print(repr(item))

            raise
        return newItem

    # Select GJ
    searchTree = xrg.idx("units","\[GJ\]")

    # Convert GJ values
    passedFunc = convertGJ_kWh
    xrg.inPlaceFunction(frame,searchTree,passedFunc,timeMask=None)

    #Update the header to match
    xrg.renameHeader(frame,searchTree,"units","*[kWh]",False,True,"\[.+\]")

    #return frame


def massConvertkWh_MWh(frame):
    # CONVERSION
    def convertkWh_MWh(item):
        if not item:
            item = "0"
        try:
            newItem = float(item) / 1000
        except:
            if item:
                print("YES")
            print(item)
            print(repr(item))
            raise
        return newItem

    # Select GJ
    searchTree = xrg.idx("units","\[kWh\]")

    # Convert GJ values
    passedFunc = convertkWh_MWh
    xrg.inPlaceFunction(frame,searchTree,passedFunc,timeMask=None)

    #Update the header to match
    xrg.renameHeader(frame,searchTree,"units","*[MWh]",False,True,"\[.+\]")


def add_row_key(row):
    keyed_row = [" ".join(row[:-1])] + row
    return keyed_row

def transpose(table):
    #print "Before rows", len(table), "cols", len(table[0])

    rowLen = len(table[0])

    last_row = None
    for row in table:
        if len(row) != rowLen:
            print("Unequal rows in table, {} should be {} \n LAST ROW: {} \n NEW ROW {}".format(len(row),rowLen,last_row,row))

            raise Exception("")
        last_row = row

    trans_table = list(zip(*table))

    return trans_table

def convert_to_float(item):
    return  item.astype(np.float)

def convert_kWh_MWh(array):
    array = array / 3000
    return array


#         {'section'      :  '',  'table' :  ''},


#--- Get extra data items
def get_end_use_subs(parseTree):
    section_name = 'Annual Building Utility Performance Summary'
    tableName = 'End Uses By Subcategory'
    table = expand_table_node(parseTree[section_name][tableName])
    #pprint(table)
    new_table = list()
    for row in table:
        label = row.pop(0) + " " +  row.pop(0)
        new_row = [label] + row
        #row.append(row)
        new_table.append(new_row)
        
    this_table = serialize_table(new_table)
    # Add the section name
    this_table = [[section_name+" End Uses"]+row for row in this_table]

    # Create a key
    this_table = [[" ".join(row[:-1])] + row for row in this_table]
    #pprint(this_table)
    
    #print_table(this_table)
    #extracted_tables = extracted_tables + this_table
    
    logging.debug("{} - {}".format(get_self(),len(this_table)))
    
    return this_table

def get_end_use_sub_demand(parseTree):
    section_name = 'Demand End Use Components Summary'
    tableName = 'End Uses By Subcategory'
    table = expand_table_node(parseTree[section_name][tableName])
    #pprint(table)
    new_table = list()
    for row in table:
        label = row.pop(0) + " " + row.pop(0)
        new_row = [label] + row
        #row.append(row)
        new_table.append(new_row)
        
    this_table = serialize_table(new_table)
    # Add the section name
    this_table = [[section_name+" End Use Demand"]+row for row in this_table]

    # Create a key
    this_table = [[" ".join(row[:-1])] + row for row in this_table]
    #pprint(this_table)
    
    #print_table(this_table)
    #extracted_tables = extracted_tables + this_table
    
    logging.debug("{} - {}".format(get_self(),len(this_table)))
    
    return this_table


def get_avg_Uvals(parseTree):
    sectionName = 'Envelope Summary'
    tableName = 'Opaque Exterior'
    table = expand_table_node(parseTree[sectionName][tableName])

    # The total area weighted U-value is the U-value multiplied by the are of each surface
    # U-value is in column 4
    # Area is in 5
    area_weighted_U = sum([float(row[4]) * float(row[5]) for row in table[1:]])
    total_area = sum([float(row[5]) for row in table[1:]])

    avgU = area_weighted_U / total_area
    oneRow = ['Item','Envelope', 'Average External U', avgU]
    oneRow = add_row_key(oneRow)
    
    logging.debug("{} - {}".format(get_self(), oneRow))
    return [oneRow]

def get_avg_window_Uval(parseTree):
    sectionName = 'Envelope Summary'
    tableName = 'Exterior Fenestration'

    table = expand_table_node(parseTree[sectionName][tableName])

    area_weighted_U = sum([float(row[7]) * float(row[2]) for row in table[1:-3]])

    total_area = sum([float(row[2]) for row in table[1:-3]])

    avgU = area_weighted_U / total_area
    one_row = add_row_key(['Item','Envelope', 'Average Window U', avgU])
    logging.debug("{} - {}".format(get_self(), one_row))
    
    return [one_row]


def get_zone_summary(parseTree):
    sectionName = 'Input Verification and Results Summary'
    tableName = 'Zone Summary'
    table = expand_table_node(parseTree[sectionName][tableName])

    rows = [
            add_row_key(['Zone Summary','Total Area', 'm2', table[-4][1]] )                  ,
            add_row_key(['Zone Summary','Conditioned Area', 'm2', table[-3][1]])             ,
            add_row_key(['Zone Summary','Unconditioned Area', 'm2', table[-2][1]])           ,
            add_row_key(['Zone Summary','Volume', '[m3]', table[-4][4]])           ,
            add_row_key(['Zone Summary','Gross Wall Area', '[m2]', table[-4][6]])           ,
            add_row_key(['Zone Summary','Window Glass Area', '[m2]', table[-4][7]])           ,
            add_row_key(['Zone Summary','Avg Lighting LPD', 'W/m2', table[-4][8]])           ,
            add_row_key(['Zone Summary','Avg Occupancy Density', 'm2/Pers', table[-4][9]])  ,
            add_row_key(['Zone Summary','Avg Plug load', 'W/m2 [-]', table[-4][10]])         ,
            ]
    
    logging.debug("{} - {}".format(get_self(), rows))

    return rows 


def get_sensible_breakdown(parseTree):
    sectionName = 'Sensible Heat Gain Summary'
    tableName = 'Annual Building Sensible Heat Gain Components'
    table = expand_table_node(parseTree[sectionName][tableName])

    results = zip(table[0][1:],table[-1][1:])

    rowkeys = [['Sensible summary', item[0],'[GJ]', item[1]] for item in results]

    rowkeys = [add_row_key(item) for item in rowkeys]

    #for rk in rowkeys:
    #    print rk


    #raise
    
    logging.debug("{} - {}".format(get_self(), rowkeys))

    return rowkeys


def get_lighting(parseTree):
    sectionName = 'Lighting Summary'
    tableName = 'Interior Lighting'

    table = expand_table_node(parseTree[sectionName][tableName])

    lastRow = table[-1]

    oneRow = ['Item','Lighting', 'Average LPD [W/m2]', lastRow[2]]
    oneRow = add_row_key(oneRow)
    logging.debug("{} - {}".format(get_self(), oneRow))
    return [oneRow]


def get_minimum_outside_air(parseTree):
    sectionName = 'Outdoor Air Summary'
    tableName = 'Minimum Outdoor Air During Occupied Hours'
    table = expand_table_node(parseTree[sectionName][tableName])

    # Header is first row, but ignore the first item (placeholder for index)
    header = [table.pop(0)][0]
    header.pop(0)

    # Index is first column
    index = [row.pop(0) for row in table]
    data = table

    flg_all_empty = False
    if len(data) == 1:
        flg_all_empty = all(len(el)==0 for el in data[0])

    if not flg_all_empty:
        frame = pd.DataFrame(data = data, index = index, columns = header)

        # Convert the numbers type='object' or type='string' to float
        frame = frame.convert_objects(convert_numeric=True)

        frame["m3h"] = frame["Mechanical Ventilation [ach]"] * frame["Zone Volume [m3]"]
        total_vent_m3h = sum(frame["m3h"])
        total_vent_m3s = total_vent_m3h/3600

    else:
        #simpleYesNo("Found no ventilation air in table")
        print("Found no ventilation air in table")
        total_vent_m3s = 0

    oneRow = ['Item',sectionName, 'Minimum outdoor air occupied [m3/s]', total_vent_m3s]
    oneRow = add_row_key(oneRow)
    logging.debug("{} - {}".format(get_self(), oneRow))
    
    return [oneRow]




def get_average_autside_air(parseTree):
    sectionName = 'Outdoor Air Summary'
    tableName = 'Average Outdoor Air During Occupied Hours'
    table = expand_table_node(parseTree[sectionName][tableName])

    # Header is first row, but ignore the first item (placeholder for index)
    header = [table.pop(0)][0]
    header.pop(0)

    # Index is first column
    index = [row.pop(0) for row in table]
    data = table

    # Create the frame
    #print "data", data
    flg_all_empty = False
    if len(data) == 1:
        flg_all_empty = all(len(el)==0 for el in data[0])

    if not flg_all_empty:
        frame = pd.DataFrame(data = data, index = index, columns = header)

        # Convert the numbers type='object' or type='string' to float
        frame = frame.convert_objects(convert_numeric=True)

        frame["m3h"] = frame["Mechanical Ventilation [ach]"] * frame["Zone Volume [m3]"]
        total_vent_m3h = sum(frame["m3h"])
        total_vent_m3s = total_vent_m3h/3600

    else:
        print("Found no ventilation air in table")

#        simpleYesNo("Found no ventilation air in table")
        total_vent_m3s = 0
#    try:
#
#    except:
#        print frame
#        print frame["m3h"]
#        print frame["Mechanical Ventilation [ach]"]
#        print frame["Zone Volume [m3]"]
    #print total_vent_m3s

    #print frame[0:10]
    #raise
#    total_vent_ach = sum(frame["Mechanical Ventilation [ach]"])
#    total_volume = sum(frame["Zone Volume [m3]"])
#    total_m3h = 1
#    print "Total vol", totalVolume
#    #print frame["Average Number of Occupants"]
#    raise
#    col = list()
#    for row in table[1:]:
#        if row[5]:
#
#            col.append(float(row[5]))
#
#        else:
#            col.append(0)
#
#    raise
#    totalAch = sum(col)
#    numEntries = len([row[5] for row in table[1:]])
#    avgAch = totalAch / numEntries
#
    oneRow = ['Item',sectionName, 'Average outdoor air occupied [m3/s]', total_vent_m3s]
    oneRow = add_row_key(oneRow)
    logging.debug("{} - {}".format(get_self(), oneRow))
    
    return [oneRow]

def get_windows(parseTree):
    sectionName = 'Envelope Summary'
    tableName = 'Exterior Fenestration'
    table = expand_table_node(parseTree[sectionName][tableName])

    # Header is first row, but ignore the first item (placeholder for index)
    header = [table.pop(0)][0]
    header.pop(0)

    # Index is first column
    index = [row.pop(0) for row in table]
    data = table

    # Create the frame
    frame = pd.DataFrame(data = data, index = index, columns = header)
    #print frame.dtypes

    # Convert the numbers type='object' or type='string' to float
    frame = frame.convert_objects(convert_numeric=True)
    #print frame.dtypes
    #print frame.index
    u_fac = frame.ix["Total or Average"]["Glass U-Factor [W/m2-K]"]
    shgc = frame.ix["Total or Average"]["Glass SHGC"]
    vis_trans = frame.ix["Total or Average"]["Glass Visible Transmittance"]

    rows = [
              add_row_key(['Item',sectionName, 'Average glass U-Factor [W/m2-K]', u_fac]),
              add_row_key(['Item',sectionName, 'Average glass SHGC', shgc]),
              add_row_key(['Item',sectionName, 'Average glass visible transmittance', vis_trans]),
              ]
    
    logging.debug("{} - {}".format(get_self(), rows))
    
    return rows


def get_zone_cooling_sizing(parseTree):
    sectionName = 'HVAC Sizing Summary'
    tableName = 'Zone Cooling'
    table = expand_table_node(parseTree[sectionName][tableName])

    # Header is first row, but ignore the first item (placeholder for index)
    header = [table.pop(0)][0]
    header.pop(0)

    # Index is first column
    index = [row.pop(0) for row in table]
    data = table

    flg_all_empty = False
    if len(data) == 1:
        flg_all_empty = all(len(el)==0 for el in data[0])

    if not flg_all_empty:
        # Create the frame
        frame = pd.DataFrame(data = data, index = index, columns = header)
        #print frame.dtypes

        # Convert the numbers type='object' or type='string' to float
        frame = frame.convert_objects(convert_numeric=True)
        #print frame.dtypes
        design_load = sum(frame["Calculated Design Load [W]"])
        user_load = sum(frame["User Design Load [W]"])
        design_air = sum(frame["Calculated Design Air Flow [m3/s]"])
        user_air = sum(frame["User Design Air Flow [m3/s]"])
    else:
        print("Found no Zone Cooling information")
        design_load = 0
        user_load = 0
        design_air = 0
        user_air = 0

    rows = [
              add_row_key(['Item',sectionName, 'Total Calculated Design Cooling Load [W]', design_load]),
              add_row_key(['Item',sectionName, 'Total User Design Cooling Load [W]', user_load]),
              add_row_key(['Item',sectionName, 'Total Calculated Design Cooling Air Flow [m3/s]', design_air]),
              add_row_key(['Item',sectionName, 'Total User Design Cooling Air Flow [m3/s]', user_air]),

              ]
    logging.debug("{} - {}".format(get_self(), rows))
              
    return rows

def get_zone_heating_sizing(parseTree):
    sectionName = 'HVAC Sizing Summary'
    tableName = 'Zone Heating'
    table = expand_table_node(parseTree[sectionName][tableName])

    # Header is first row, but ignore the first item (placeholder for index)
    header = [table.pop(0)][0]
    header.pop(0)

    # Index is first column
    index = [row.pop(0) for row in table]
    data = table

    flg_all_empty = False
    if len(data) == 1:
        flg_all_empty = all(len(el)==0 for el in data[0])

    if not flg_all_empty:
        # Create the frame
        frame = pd.DataFrame(data = data, index = index, columns = header)
        #print frame.dtypes

        # Convert the numbers type='object' or type='string' to float
        frame = frame.convert_objects(convert_numeric=True)
        #print frame.dtypes
        design_load = sum(frame["Calculated Design Load [W]"])
        user_load = sum(frame["User Design Load [W]"])
        design_air = sum(frame["Calculated Design Air Flow [m3/s]"])
        user_air = sum(frame["User Design Air Flow [m3/s]"])
    else:
        print("Found no Zone Heating information")
        design_load = 0
        user_load = 0
        design_air = 0
        user_air = 0

    rows = [
              add_row_key(['Item',sectionName, 'Total Calculated Design Heating Load [W]', design_load]),
              add_row_key(['Item',sectionName, 'Total User Design Heating Load [W]', user_load]),
              add_row_key(['Item',sectionName, 'Total Calculated Design Heating Air Flow [m3/s]', design_air]),
              add_row_key(['Item',sectionName, 'Total User Design Heating Air Flow [m3/s]', user_air]),

              ]
    logging.debug("{} - {}".format(get_self(), rows))
    
    return rows

def get_title(thisTableFileName, searchHeading):
    root = lxml.html.parse(thisTableFileName)
    node = root.xpath("//p[text() = '{}']".format(searchHeading))[0]

    nextBold = node.xpath("b")[0]

    return nextBold.text.strip()

#--- Process

def serialize_table(table_rows):
    """
    Serialize a 2d table down into a column of [header label, row label, data item]
    """
    #print("asdfasdfdas")
    #pprint(table_rows)
    
    target_length = 3
    # Get the headers, the first row, skipping the blank column where the names are
    headers = table_rows.pop(0)[1:]

    # The names of each row are the first
    row_labels = [row.pop(0) for row in table_rows]

    # What's left over is the data
    data = table_rows

    flat_table = list()
    # Loop over rows, then columns, keeping the indices for the data elements
    for idx1,row_name in enumerate(row_labels):
        for idx2,col_name in enumerate(headers):
            flat_table.append([row_name, col_name,data[idx1][idx2]])

    for row in flat_table:
        if target_length != len(row):
            raise Exception("Wrong length of {} is less than target_length {} ".format(row,target_length))




    #compare_length = len(flat_table[0])

    #for row in flat_table:
    #    assert(len(row)==compare_length), "Length of first row {}, this length {}".format(compare_length,len(row))
    length_set = set(map(len, flat_table))


    logging.debug("Serialized table, size {}".format(length_set))

    assert(len(length_set) == 1), "ERROR {}".format(table_rows)

    return flat_table


def expand_table_node(node):
    """
    Convert a table node into a 2D array of table values
    """
    table_rows = list()
    # Loop over rows
    for tr in node:

        #print tr
        thisRow = list()

        # Loop over items in row
        for td in tr.xpath('td'):
            # Get the item
            if td.text:
                text=td.text.strip()
            else:
                text = ""

            # Append items
            thisRow.append(text)
        # Append rows
        table_rows.append(thisRow)

    return table_rows


def get_one_table(tree, section_name,table_name):

    # Make sure the table exists
    if section_name not in  tree:
        raise KeyError("'{}' not in section names".format(section_name))
    if table_name not in tree[section_name]:
        raise KeyError("'{}' not in tables of '{}' section".format(table_name,section_name))

    # First, go to this html node and get all the rows and data from the table
    this_table = expand_table_node(tree[section_name][table_name])

    logging.debug("Returning {} - {}, {} rows, {} cols".format(section_name,table_name, len(this_table),len(this_table[0])))

    return this_table

def extract_tables(tree):
    """This function iterates over all table definitions i.e.:
        {'section'     :   'Annual Building Utility Performance Summary',  'table'       :   'Site and Source Energy'  }
    First, the data is collected as a 2D table, converted into python
    Second, this 2D table is serialized for excel, i.e.: 
        row_name, col_name, data
    """
    extracted_tables = list()
    
    for table_def in TABLES:
        # Get the definition
        section_name = table_def['section']
        table_name = table_def['table']

        logging.debug("Getting table {} - {}".format(section_name,table_name))

        this_table = get_one_table(tree, section_name,table_name)
        
        # Then take this newly updated dictionary entry and serialize it
        this_table = serialize_table(this_table)

        # Add the section name
        this_table = [[section_name]+row for row in this_table]

        # Create a key
        this_table = [[" ".join(row[:-1])] + row for row in this_table]
        #print_table(this_table)
        extracted_tables = extracted_tables + this_table
        
    logging.debug("Processed tables into {} serial data rows".format(len(extracted_tables)))
    return extracted_tables




def get_zone_summary_tables(inputDir):

    #outputFile = inputDir + r"\00results"

    htmlFilePaths =  filter_files_dir(inputDir,ext_pat="html$")
    comparison_frame = None
    assert(len(htmlFilePaths) != 0), "No html files found"

    tables_dict = dict()

    # Loop over files
    df_dict = dict()
    for path_file in htmlFilePaths:
        
        #print(path_file)
        split_path = util_paths.split_up_path(path_file)
        extension = split_path.pop()
        name = split_path.pop()
        
        #name = re.sub(r'-', r'', name)
        #name = re.sub(r'G000', r'', name)
        #name = re.sub(r'0', r'', name)
        name = re.sub(r'Table', r'', name)
        
        logging.debug("Processing {} at {}".format(name,path_file,))

        
        #out_file_name = name + "Zone Summary dataframe.pck"
        
        #out_file_path_pck = inputDir + "\\" + out_file_name
        #out_file_path_xlsx = inputDir + "\\Zone summaries.xlsx"
        
        # The tree is a dict of dicts, by [section_name][table_name] = NODE ELEMENT
        tree = parse_file(path_file)

        section_name = 'Input Verification and Results Summary'
        table_name = 'Zone Summary'

        this_table = get_one_table(tree, section_name,table_name)

        headers = this_table.pop(0)
        headers = headers[1:]
        zone_names = [row.pop(0) for row in this_table]
        
        #=======================================================================
        # Get frame
        #=======================================================================
        this_frame = pd.DataFrame(this_table,index = zone_names, columns = headers)
        this_frame.index.name = "Zone name"

        #=======================================================================
        # Drop the summary rows
        #=======================================================================
        drop_rows = ['Total','Conditioned Total','Unconditioned Total','Not Part of Total']
        this_frame.drop(this_frame.loc[drop_rows,:].index, inplace = True)

        #=======================================================================
        # Update the Yes No to bool, convert numeric
        #=======================================================================
        yn = {'Yes': True, 'No': False}
        this_frame['Conditioned (Y/N)'].replace(yn,inplace=True)
        this_frame['Part of Total Floor Area (Y/N)'].replace(yn,inplace=True)
        new_frame = this_frame.convert_objects(convert_numeric=True)
        
        tables_dict[name] = new_frame

        logging.debug("Zone summary dataframe over {} zones".format(len(new_frame.index)))
        
        
        #=======================================================================
        # Save to pck
        #=======================================================================
        #new_frame.to_pickle(out_file_path_pck)
        #df_dict[name] = new_frame

        #=======================================================================
        # Save to mat
        #=======================================================================

        #out_file_name = name + "Zone Summary dataframe.mat"

        #out_file_path_mat = inputDir + "\\" + out_file_name
        #xrg2.write_matlab_frame(new_frame,out_file_path_mat,name = name)
        
        #logging.debug("Saved zone summary information to {}".format(out_file_path_pck))

    #===========================================================================
    # Save to xlsx
    #===========================================================================
    #xrg2.write_dict_to_excel(df_dict, out_file_path_xlsx)
    logging.debug("Retrieved {} zone summary table into dataframes in {}".format(len(df_dict),inputDir))
    return tables_dict


def augment_data_tables(extracted_tables,tree):

    extracted_tables = extracted_tables + get_lighting(tree)
    extracted_tables = extracted_tables + get_avg_Uvals(tree)
    extracted_tables = extracted_tables + get_avg_window_Uval(tree)
    extracted_tables = extracted_tables + get_zone_summary(tree)
    extracted_tables = extracted_tables + get_sensible_breakdown(tree)
    extracted_tables = extracted_tables + get_average_autside_air(tree)
    extracted_tables = extracted_tables + get_minimum_outside_air(tree)
    extracted_tables = extracted_tables + get_windows(tree)
    extracted_tables = extracted_tables + get_end_use_subs(tree)    
    extracted_tables = extracted_tables + get_end_use_sub_demand(tree)
    
    #pprint(get_end_use_sub_demand(tree))
    #raise 
    try: 
        extracted_tables = extracted_tables + get_zone_cooling_sizing(tree)
        extracted_tables = extracted_tables + get_zone_heating_sizing(tree)
    except: 
        pass
    
    return extracted_tables

def validate_tables(extracted_tables):
    # Check lengths are equal
    last_length = None
    for row in extracted_tables:
        #print(row)
        if not last_length:
            last_length = len(row)
            continue
        #assert(len(row) == last_length), "Length of this row is {}, last row {}, {}".format(len(row),last_length,row)

def parse_html_to_excel_summary(inputDir,loc_post_excel):
    """Main script
    #

    """
    
    logging.debug("Processing {} {}".format(inputDir,loc_post_excel))

    outputFile = inputDir + r"\00results"
    xlsFullPath = outputFile + ".xlsx"

    htmlFilePaths =  filter_files_dir(inputDir,ext_pat="html$")
    assert(len(htmlFilePaths) != 0), "No html files found"

    tables_list = list()
    # Loop over files
    index_array = list()
    for path_file in htmlFilePaths:

        logging.debug("Processing {}".format(path_file))

        #--- 1. Get tree structure as lxml 
        # The tree is a dict of dicts, by [section_name][table_name] = NODE ELEMENT
        tree = parse_file(path_file)

        #--- 2. Process html node into a python data structure
        extracted_tables = list()
        extracted_tables = extract_tables(tree)

        logging.debug("Finished processing {}".format(extracted_tables))

        ### Finished with all tables
        
        # Get the title element
        title = get_title(path_file, "Building: ")
        
        
        #--- 3. Augment table with summary items()
        extracted_tables = augment_data_tables(extracted_tables,tree)
        
        
        #--- Extra processing for title, to add the rotation angle
        for row in extracted_tables:
            if row[0] == "Input Verification and Results Summary Rotation for Appendix G [deg] Value":
                rotation = row[-1]
                rotation = str(int(float(rotation)))
        if "Proposed" not in title:
            title = title + " " + rotation

        index_array.append(title)
        
        #--- 4. Validate tables
        validate_tables(extracted_tables)

        # Done with this file
        tables_list.append(extracted_tables)

    #--- Process each resulting list from each file
    headers_def = ["key","section","table","units"]
    
    data = list()
    
    headers = None

    #--- Assemble one big data array
    for i,this_table in enumerate(tables_list):
        print(i)
        data.append([row.pop() for row in this_table])
        #print(len(this_table))
        #print(len(this_table[0]))        
        if headers == None:
            headers=transpose(this_table)
        else:
            # TODO: Why was this assertion here? Why did it cause problems suddenly? 
            #assert(headers == transpose(this_table))
            if not headers == transpose(this_table):
            #except:
                print("Error in {}th table".format(i))
                #print_table(this_table)
                print("HEADERS: {} x {}".format(len(headers), len(headers[0])))
                #print
                #print_table(headers[1])
                print("TABLE:")
                print_table(this_table[:3])
                #raise
                

    #--- Create MI Dataframe
    # Transpose
    data = list(zip(*data))
    
    # Write unique column names
    #integers = list(range(0,5))
    #zipped = list(zip(index_array,integers,))
    #print(zipped)
    #raise
    #column_names = [item[0]+str(item[1]) for item in zipped]
    column_names = index_array
    
    m_index = pd.MultiIndex.from_arrays(headers,names = headers_def)
    df = pd.DataFrame(data = data, index = m_index,columns = column_names)
    
    #--- Conversions
    #massConvertGJ_kWh(comparison_frame)
    #massConvertkWh_MWh(comparison_frame)

    #--- Write the file
    

    #df.to_excel(writer)
    #writer.save()
    #raise

    util_paths.copy_file(loc_post_excel,xlsFullPath)
    book = load_workbook(xlsFullPath)
    writer = pd.ExcelWriter(xlsFullPath, engine='openpyxl')
    writer.book = book
    writer.sheets = dict((ws.title, ws) for ws in book.worksheets)

    sheet_name = 'DATABASE'
    
    df.to_excel(writer, sheet_name = sheet_name, startrow = 0, startcol = 0)
    
    writer.save()
    
    logging.debug("Wrote df size {} to {}".format(df.shape,xlsFullPath))

    #raise



def parse_file(thisTableFileName,flg_verbose = False):
    """
    Given an EnergyPlus HTML file name;
    Break up the table into a dictionary tree
    Tree contains the lxml nodes of the relevant tables
    """

    # Root node
    root = lxml.html.parse(thisTableFileName)

    # Select all sections
    sections = root.xpath("//p[text() = 'Report:']")
    sectionDict = {}
    numTables = 0

    # Loop over sections
    for sect in sections:

        # Get the section name
        sectionName = sect.xpath("b")

        patValue = r".*Monthly$"
        regex = re.compile(patValue,re.VERBOSE)
        if regex.match(sectionName[0].text):
            print("SkipMonthly",)
            continue

        if flg_verbose:
            print(sectionName[0].text)
        assert len(sectionName) == 1
        sectionName = sectionName[0]
        sectionNameText= sectionName.text.strip()


        flgContinue = True
        count = 0
        currentNode = sectionName.getparent()

        tables = dict()

        while 1:
            # Loop over the nodes
            currentNode = currentNode.getnext()

            # If there is no node, break the loop
            if currentNode == None:
                break

            # If the section is finished (we see the next section) break the loop
            if currentNode.xpath("text() = 'Report:'"):
                flgContinue = False
                break

            # If we see too many iterations, break
            count += 1
            if count > 1000000:
                flgContinue = False

            # If this is a table, process the table
            if currentNode.tag == "table":
                # Get the name
                # Get all the <b> elements, since the title is bold
                # We just selected ALL previous <b>, and we want only the one right before, hence -1
                tableName = currentNode.xpath("preceding-sibling::b")[-1]

                # Apply this table to the dict
                tables[tableName.text] = currentNode

        # This section is finished
        sectionDict[sectionNameText] = tables
        numTables = numTables + len(tables)
        
    logging.info("Parsed {} tables from {} sections to dictionary".format(numTables,len(sectionDict)))

    return sectionDict

def parse_file2(thisTableFileName,flg_verbose = False):
    """
    Updated to capture more information from the HTML file. 
    
    Now, each section has a 'preamble' and 'tables' entry. 
    
    """
    myLogger.setLevel("DEBUG")
    
    logging.debug("Start parse")
    
    # Root node
    root = lxml.html.parse(thisTableFileName)
    
    # Select all sections
    sections = root.xpath("//p[text() = 'Report:']")
    sectionDict = {}
    numTables = 0
    
    # Loop over sections
    for sect in sections:

        # Get the section name
        section_node_list = sect.xpath("b")
        assert len(section_node_list) == 1
                
        section_node = section_node_list[0]
        
        #print(type(section_node))
        
        
        # Skip any monthly summary reports
        patValue = r".*Monthly$"
        regex = re.compile(patValue,re.VERBOSE)
        if regex.match(section_node.text):
            print("SkipMonthly",)
            continue
        
        section_name = section_node.text.strip()
        logging.debug("Section: {}".format(section_name))
        
        # Start this dictionary for this current section
        sectionDict[section_name] = dict()

        # Step up to the <p>Report:
        current_node = section_node.getparent()
        line3_report_title = tostring(current_node)
        #print(current_node.text)
        
        #Step back to <a href>
        current_node = current_node.getprevious()
        line2_toc_link = tostring(current_node)
        
        #Step back to <p><toc>
        current_node = current_node.getprevious()
        line1_toc_link = tostring(current_node)
        
        print(line1_toc_link)
        print(line2_toc_link)
        print(line3_report_title)
        current_node = section_node.getparent()

        current_node = current_node.getnext()
        line4_toc_link = tostring(current_node)
        print(line4_toc_link)
        
        current_node = current_node.getnext()
        line5_timestamp = tostring(current_node)
        print(line5_timestamp)
        
        report_preamble = [
            line1_toc_link,
            line2_toc_link,
            line3_report_title,
            line4_toc_link,
            line5_timestamp,
            ]
        sectionDict[section_name]['preamble'] = report_preamble

        #raise

        flgContinue = True
        count = 0
        tables = dict()
        current_node = section_node.getparent()
        while 1:
            # Loop over the nodes
            current_node = current_node.getnext()

            # If there is no node, break the loop
            if current_node == None:
                break

            # If the section is finished (we see the next section) break the loop
            if current_node.xpath("text() = 'Report:'"):
                flgContinue = False
                break

            # If we see too many iterations, break
            count += 1
            if count > 1000000:
                flgContinue = False

            # If this is a table, process the table
            if current_node.tag == "table":
                # Get the name
                # Get all the <b> elements, since the title is bold
                # We just selected ALL previous <b>, and we want only the one right before, hence -1
                tableName = current_node.xpath("preceding-sibling::b")[-1]

                #tableName = current_node.xpath("preceding-sibling::b")[-1]

                # Apply this table to the dict
                tables[tableName.text] = current_node

        # This section is finished
        #sectionDict[section_name] = tables\
        numTables = numTables + len(tables)
        
        sectionDict[section_name]['tables'] = tables
    
    logging.info("Parsed {} tables from {} sections to dictionary".format(numTables,len(sectionDict)))
    raise
    return sectionDict




def run_projectGUI():

    from UtilityGUI import runDirectory
    import wx

    HTMLdataDir = r"C:\Projects\IDFout"
    #HTMLdataDir = r"C:\Dropbox\BREEAM ENE 5 Results1"


    app = wx.App(False)
    frame = runDirectory(HTMLdataDir, parse_html_to_excel_summary)
    frame.Show()
    app.MainLoop()


#===============================================================================
# Main
#===============================================================================
if __name__ == "__main__":
    print(ABSOLUTE_LOGGING_PATH)
    logging.config.fileConfig(ABSOLUTE_LOGGING_PATH)


    myLogger = logging.getLogger()
    myLogger.setLevel("DEBUG")

    logging.debug("Started _main".format())
    HTMLdataDir = r"C:\Projects\IDFout"

    if 0:
        HTML_template_dir = get_latest_rev(r"C:\Projects\IDF_Library\01 Post Process excel", r"^LEED PostProcess", ext_pat = "xlsx")


        shutil.copy(HTML_template_dir, HTMLdataDir)

        #HTML_template_dir = excelProjectDir = get_latest_rev(r"HTMLdataDir", r"^LEED PostProcess", ext_pat = "xlsx")

        target_report_path = get_latest_rev(HTMLdataDir, r"^LEED PostProcess", ext_pat = "xlsx")

        wb = ExtendedExcelBookAPI(target_report_path)
        with ExtendedExcelBookAPI(target_report_path) as excel:
            #print excel.book
            assert(excel.sheetExists(u'DATABASE'))
            sheet = excel.book.Sheets(u'DATABASE')
            #print sheet.Cells(1,1).Value
            last_row = excel.scanDown2(u'DATABASE', 1, 1, "None", limitScan=100000)
        raise
        #book = xlrd.open_workbook(target_report_path)
        #print book.sheet_names()
        #sh = book.sheet_by_name(u'DATABASE')
        #print sh
        #for row in sh:
        #    print row
        #excel_template = ExtendedExcelBookAPI(HTML_template_dir)
        #excel_template.getSheetNames()

        #print xlwt

        #print HTML_template_dir

        #raise
        #run_projectGUI()
        #parse_html_to_excel_summary(HTMLdataDir)

    parse_html_to_excel_summary(HTMLdataDir)

    logging.debug("Finished _main".format())
