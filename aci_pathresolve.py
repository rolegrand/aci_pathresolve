#!/usr/bin/env python

from creds import *
import cobra.mit.session
import cobra.mit.access
import cobra.mit.request
import cobra.model.phys
import cobra.modelimpl.fv.attentitypathatt
import cobra.modelimpl.fv.stpathatt
import cobra.modelimpl.fv.extstpathatt
import requests
import time
import argparse
# import pandas as pd
requests.packages.urllib3.disable_warnings()

mydict = {}


def read_ext_file():
    ## Reading external file to test extrating options
    f = open("aci_path_hpr.conf", "r")
    # print(f.read())
    for i in f:
        port_list = []
        tenant_name, epg_name, node_name, port_list = extractinfo(i, port_list)
        dict_building(tenant_name, epg_name, node_name, port_list)


def dict_building(tenant_name, epg_name, node_name, port_list):
    if epg_name == 'none':
        pass
    else:
        mydict[tenant_name + '-' + epg_name] = {'tenant_name': tenant_name,
                                                'epg_name': epg_name,
                                                'node_name': node_name,
                                                'port_name': port_list}

    return mydict


def extractinfo(input, port_list):
    tenant_name = input.split('tn-', 1)[1].split('/')[0]
    epg_name = input.split('epg-', 1)[1].split('/')[0]
    node_name = input.split('node-', 1)[1].split('/')[0]

    if 'aggr-' in input:
        port_name = input.split('aggr-[', 1)[1].split(']')[0]
        port_list.append(port_name)
    elif 'phys-' in input:
        port_name = input.split('phys-[', 1)[1].split(']')[0]
        port_list.append(port_name)
    else:
        port_name = 'no_match'
        port_list.append(port_name)

    return tenant_name, epg_name, node_name, port_list

def DeploymentQuery(session, mydict, epg):
    port_list = []
    defquery1 = cobra.mit.request.DeploymentQuery(epg)
    defquery1.targetPath = 'EPgToNwIf'
    defquery1.targetNode = 'all'
    testquery = session.query(defquery1)[0]

    for i in testquery.children:
        for j in i.children:
            tenant_name, epg_name, node_name, port_list = extractinfo(str(j.dn), port_list)

    try:
        node_name
        epg_name
        tenant_name
    except NameError:
        node_name = 'none'
        epg_name = 'none'
        tenant_name = 'none'

    dict_building(tenant_name, epg_name, node_name, port_list)
    return mydict

def main():
    auth = cobra.mit.session.LoginSession(URL, LOGIN, PASSWORD, secure=False)
    session = cobra.mit.access.MoDirectory(auth)
    session.login()

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tenant')
    parser.add_argument('-e', '--epg')
    parser.add_argument('-d', '--debug')

    args = parser.parse_args()

    tenant_input_filter = args.tenant
    epg_input_filter = args.epg
    debug_input_filter = args.debug

    epg_query_def = cobra.mit.request.ClassQuery('fvAEPg')
    # Bulding argparse filters
    if debug_input_filter is not None:
        read_ext_file()
    else:
        if tenant_input_filter and epg_input_filter is not None:
            epg_query_def.propFilter = 'and(wcard(fvAEPg.dn, "{}")wcard(fvAEPg.dn,"{}"))'.format('tn-' + tenant_input_filter, 'epg-' + epg_input_filter)
        elif tenant_input_filter is not None:
            epg_query_def.propFilter = 'wcard(fvAEPg.dn, "{}")'.format('tn-' + tenant_input_filter)
        elif epg_input_filter is not None:
            epg_query_def.propFilter = 'wcard(fvAEPg.dn, "{}")'.format('epg-' + epg_input_filter)
        epg_query = session.query(epg_query_def)

        for epg in epg_query:
            DeploymentQuery(session, mydict, epg.dn)

    # pd_mydict = pd.DataFrame.from_dict(mydict, orient='index')
    # pd_mydict.to_excel('results.xlsx')
    result_read(mydict)

def result_read(mydict):
    print('{:<48} {:<48} {:<48} {:<48}'.format('TENANT', 'EPG', 'NODE', 'PORT_LIST'))
    for k, v in mydict.items():
        tenant_name, epg_name, node_name, port_name = v['tenant_name'], v['epg_name'], v['node_name'], v['port_name']
        print('{:<48} {:<48} {:<48} {:<48}'.format(tenant_name, epg_name, node_name, str(port_name)))


if __name__ == "__main__":
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))