import pandas as pd
import psycopg2, argparse, os, subprocess, json, csv, time, sys, re, requests, boto3
from IPython.display import display
from pathlib import Path
from subprocess import check_output
from bs4 import BeautifulSoup
import warnings

# remove Future Warning text -
warnings.filterwarnings('ignore')
# remove in case need to debug
#sys.tracebacklimit = 0

class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

class get:
 
    parser = argparse.ArgumentParser(prog="search_ORG.py", description="Orca App for Support")
    # set arguments
    parser.add_argument("-org_name", help="org_name will search for the Organization by Name in DB", nargs=1, metavar=('organization_name'))
    parser.add_argument("-org_id", help="org_id will search for the Organization by ID in DB, must use the full organization ID", nargs=1, metavar=('organization_id'))
    parser.add_argument("-prov_id", help="prov_id will search for the Account by ID in DB, must use the full provider ID/Project Name", nargs=1, metavar=('provider_id'))
    parser.add_argument("-cloudaccount", help="Find the CloudAccount via the Orca cloudaccount_id", nargs=1, metavar=('cloudaccount_id'))
    parser.add_argument("-k8s", help="Find the Kubernetes cluster using the provider_id", nargs=1, metavar=('provider_id'))
    parser.add_argument("-k8s_conn", help="Test k8s connectivity, getting a command to run using <provider_id cluster_name>", nargs=2, metavar=('provider_id','cluster_name'))
    parser.add_argument("-user", help="Searching a User in the DB", nargs=1, metavar=('email_address'))
    parser.add_argument("-role", help="Searching a role of a User in the DB", nargs=1, metavar=('email_address'))
    parser.add_argument("-notification", help="Get Notification by Org ID", nargs=1, metavar=('organization_id'))
    parser.add_argument("-preset", help="preset will search any Preset in DB", nargs=1, metavar=('org_name'))
    parser.add_argument("-invite", help="invite will search any Invite with a specific email in DB", nargs=1, metavar=('email_address'))
    parser.add_argument("-aws_conf", help="Provide aws_config data using the provider ID, in order to use aws cli", nargs=1, metavar=('provider_id'))
    parser.add_argument("-gcp_conf", help="Provide gcp_config data using the GCP Project name, in order to use gcloud cli", nargs=1, metavar=('provider_id'))
    parser.add_argument("-res_col", help="Provide the next values <provider_id asset_id jwt-token> to create a Reserve Collector", nargs=3, metavar=('provider_id','asset_id','jwt-token'))
    parser.add_argument("-res_s3", help="Provide the next values <provider_id bucket_name jwt-token> to create a S3 Bucket Reserve Collector", nargs=3, metavar=('provider_id','bucket_name','jwt-token'))
    parser.add_argument("-res_fargate", help="Provide the next values <provider_id fargate_asset_id jwt-token> to create a Fargate Cluster Reserve Collector", nargs=3, metavar=('provider_id', 'fargate_asset_id', 'jwt-token'))
    parser.add_argument("-allow_reg", help="", nargs=1, metavar=('profile'))
    parser.add_argument('--geo', help="Use Specific DB <us OR eu OR ap>", nargs=1, metavar=('region'))
    
    
    args = parser.parse_args()

    geo_search = getattr(args, "geo")
    orgName_search = getattr(args, "org_name")
    orgID_search = getattr(args, "org_id")
    preset_search = getattr(args, "preset")
    user_search = getattr(args, "user")
    role_search = getattr(args, "role")
    invite_search = getattr(args, "invite")
    provider_id_search = getattr(args, "prov_id")
    provider_id = getattr(args, "aws_conf")
    gcp_id = getattr(args, "gcp_conf")
    cloudaccount_id_search = getattr(args, "cloudaccount")
    notification_search = getattr(args, "notification")
    k8s_search = getattr(args, "k8s")
    profile_search = getattr(args, "allow_reg")


    home_folder = os.environ.get("HOME")
    orca_folder = os.environ.get("SRC_ROOT")

class var:
    file = get.home_folder + "/Desktop/Search.html"
    aws_file = get.home_folder + "/.aws/config"
    orca_reg_link = "https://app.orcasecurity.io/register?invite_code="
    csv_file = get.home_folder + "/Desktop/Search.csv"

class ApiDB:

    def query_api_db(self, query, port):
        # remove Future Warning text - remove in case need to debug
        #sys.tracebacklimit = 0

        vals = get_val(get.home_folder + "/.secret/secrets.json")
        user = vals['user']
        password = vals['password']

        database = "postgres"
        user = user
        password = password
        host = "localhost"
        try:
            conn = psycopg2.connect(database=database, user=user, password=password, host=host, port=port,
                                    connect_timeout=5)
            df = pd.read_sql(con=conn, sql=query)
            pd.set_option("display.max_colwidth", 199)
            return df
        except psycopg2.OperationalError as error:
            error_msg = str(error)
            if "server closed" or "Connection refused" or "timed out" in error_msg:
                print(bcolors.FAIL + "All Tunnels are down, Resetting AllTunnels please wait..." + bcolors.ENDC)
                get_pid_tun_us = subprocess.Popen(
                    "lsof -i :9000 | grep 'localhost:cslistener (LISTEN)' | grep -v 'PID' | awk '{print $2; exit}'",
                    shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                out_us, err = get_pid_tun_us.communicate()
                get_pid_tun_eu = subprocess.Popen(
                    "lsof -i :9001 | grep 'localhost:etlservicemgr (LISTEN)' | grep -v 'PID' | awk '{print $2; exit}'",
                    shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                out_eu, err = get_pid_tun_eu.communicate()
                get_pid_tun_au = subprocess.Popen(
                    "lsof -i :9002 | grep 'localhost:dynamid (LISTEN)' | grep -v 'PID' | awk '{print $2; exit}'",
                    shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                out_au, err = get_pid_tun_au.communicate()

                pid_us_str = out_us.decode()
                pid_eu_str = out_eu.decode()
                pid_au_str = out_au.decode()
                pid_us = pid_us_str[:-1]
                pid_eu = pid_eu_str[:-1]
                pid_au = pid_au_str[:-1]

                kill_tun = subprocess.Popen(f"kill {pid_us} {pid_eu} {pid_au}", shell=True, executable="/bin/zsh",
                                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                kill, err = kill_tun.communicate()

                tunnel()
                try:
                    conn = psycopg2.connect(database=database, user=user, password=password, host=host, port=port,
                                            connect_timeout=10)
                    df = pd.read_sql(con=conn, sql=query)
                    pd.set_option("display.max_colwidth", 199)
                    return df
                except psycopg2.OperationalError as error:
                    error_msg = str(error)
                    if "server closed" or "Connection refused" or "timed out" in error_msg:
                        print(bcolors.FAIL + "Please check your Internet connection and try again" + bcolors.ENDC)
            elif "password authentication failed" in error_msg:
                print(
                    bcolors.FAIL + "Please check your secret file (~/.secret) and confirm User and Password are correct" + bcolors.ENDC)
            else:
                print(bcolors.FAIL + "Please check your Internet connection and try again" + bcolors.ENDC)
                # print(error_msg)

    def query_api_db_ap(self, query, port):
        # remove Future Warning text - remove in case need to debug
        #sys.tracebacklimit = 0

        vals = get_val(get.home_folder + "/.secret/secrets.json")
        user = vals['user']
        password = vals['password']

        database = "orca"
        user = user
        password = password
        host = "localhost"
        try:
            conn = psycopg2.connect(database=database, user=user, password=password, host=host, port=port,
                                    connect_timeout=5)
            df = pd.read_sql(con=conn, sql=query)
            pd.set_option("display.max_colwidth", 199)
            return df
        except psycopg2.OperationalError as error:
            error_msg = str(error)
            if "server closed" or "Connection refused" or "timed out" in error_msg:
                print(bcolors.FAIL + "AU Tunnel is down, Resetting AU Tunnel please wait..." + bcolors.ENDC)

                get_pid_tun_au = subprocess.Popen(
                    "lsof -i :9002 | grep 'localhost:dynamid (LISTEN)' | grep -v 'PID' | awk '{print $2; exit}'",
                    shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                out_au, err = get_pid_tun_au.communicate()

                pid_au_str = out_au.decode()
                pid_au = pid_au_str[:-1]

                kill_tun = subprocess.Popen(f"kill {pid_au}", shell=True, executable="/bin/zsh",
                                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                kill, err = kill_tun.communicate()

                tunnel()
                try:
                    conn = psycopg2.connect(database=database, user=user, password=password, host=host, port=port,
                                            connect_timeout=10)
                    df = pd.read_sql(con=conn, sql=query)
                    pd.set_option("display.max_colwidth", 199)
                    return df
                except psycopg2.OperationalError as error:
                    error_msg = str(error)
                    if "server closed" or "Connection refused" or "timed out" in error_msg:
                        print(bcolors.FAIL + "Please check your Internet connection and try again" + bcolors.ENDC)
            elif "password authentication failed" in error_msg:
                print(
                    bcolors.FAIL + "Please check your secret file (~/.secret) and confirm User and Password are correct" + bcolors.ENDC)
            else:
                print(bcolors.FAIL + "Please check your Internet connection and try again" + bcolors.ENDC)
                # print(error_msg)

    def query_all_regions(self, query, regions="all"):
        aws_connect()
        tunnel()
        #sys.tracebacklimit = 0
        ports = []
        if regions == "all":
            ports = [9000, 9001, 9002]
        if "us" in regions:
            ports.append(9000)
        if "eu" in regions:
            ports.append(9001)
        if "ap" in regions:
            ports.append(9002)
        ret = pd.DataFrame()
        for port in ports:
            if port == 9000:
                df = self.query_api_db(query, port=port)
                if df is not None:
                    df["region"] = "us"
                else:
                    exit()
            elif port == 9001:
                df = self.query_api_db(query, port=port)
                if df is not None:
                    df["region"] = "eu"
                else:
                    exit()
            elif port == 9002:
                df = self.query_api_db_ap(query, port=port)
                if df is not None:
                    df["region"] = "ap"
                else:
                    exit()
            ret = pd.concat([ret, df], ignore_index=True)
        return ret

class options:


    def org_name():
        orgName_str = get.orgName_search[0]
        
        if get.geo_search != None:
            if get.geo_search[0] != 'us' and get.geo_search[0] != 'eu' and get.geo_search[0] != 'ap':
                print(
                    "The argument " + bcolors.FAIL + '--geo' + bcolors.ENDC + " can only be: " + bcolors.FAIL + "us, eu, ap" + bcolors.ENDC)
                exit()
            df = ApiDB().query_all_regions(query=f"""select name,id,customer_type from api_organization where lower(name) like '%{orgName_str}%' limit 20""", regions=get.geo_search[0])
        else:
            df = ApiDB().query_all_regions(query=f"""select name,id,customer_type from api_organization where lower(name) like '%{orgName_str}%' limit 20""")

        if df.empty:
            print(bcolors.FAIL + "No Organization Found" + bcolors.ENDC)
            exit()
        else:
            html(df)
            text = "<strong> Organizations found:</strong> \n\n"
            txt_html(text)

            print(bcolors.OKBLUE + "We found Organization in our search" + bcolors.ENDC)
            display(df)
            print(bcolors.OKGREEN + "To see search result open: " + bcolors.ENDC + var.file)

    def org_id():
        orgID_str = get.orgID_search[0]
        # confirm orgID_str is per UUID example - 7c9ee3e1-bbea-447f-853c-c53b9b190240
        if not re.match(r"^[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}$",
                        orgID_str):
            print(bcolors.FAIL + "UUID is not valid, please verify the ORG id" + bcolors.ENDC)
        else:
            if get.geo_search != None:
                if get.geo_search[0] != 'us' and get.geo_search[0] != 'eu' and get.geo_search[0] != 'ap':
                    print(
                        "The argument " + bcolors.FAIL + '--geo' + bcolors.ENDC + " can only be: " + bcolors.FAIL + "us, eu, ap" + bcolors.ENDC)
                    exit()
                else:
                    df5 = ApiDB().query_all_regions(query=f"""select name,id,customer_type from api_organization where (id) = '{orgID_str}' limit 20""", regions=get.geo_search[0])
            else:
                df5 = ApiDB().query_all_regions(query=f"""select name,id,customer_type from api_organization where (id) = '{orgID_str}' limit 20""")

            if df5.empty:
                print(bcolors.FAIL + "No Organization Found with provided ID" + bcolors.ENDC)
                exit()
            else:
                html(df5)
                text = "<strong> Organizations found:</strong> \n\n"
                txt_html(text)

                print(bcolors.OKBLUE + "We found Organization in our search" + bcolors.ENDC)
                display(df5)
                print(bcolors.OKGREEN + "To see search result open: " + bcolors.ENDC + var.file)

    def k8s():
        k8s_str = get.k8s_search[0]

        if get.geo_search != None:
            if get.geo_search[0] != 'us' and get.geo_search[0] != 'eu' and get.geo_search[0] != 'ap':
                print(
                    "The argument " + bcolors.FAIL + '--geo' + bcolors.ENDC + " can only be: " + bcolors.FAIL + "us, eu, ap" + bcolors.ENDC)
                exit()
            else:
                df10 = ApiDB().query_all_regions(query=f"""select id from api_cloudaccount where (cloud_provider_id) = '{k8s_str}' limit 20""", regions=get.geo_search[0])
        else:
            df10 = ApiDB().query_all_regions(query=f"""select id from api_cloudaccount where (cloud_provider_id) = '{k8s_str}' limit 20""")
        
        if df10.empty:
            print(bcolors.FAIL + "No CloudAccount ID Found with provided ID" + bcolors.ENDC)
            exit()
        else:
            account_id = df10['id'][0]
            if get.geo_search != None:
                df5 = ApiDB().query_all_regions(query=f"""select cluster_name,id,cluster_type,location,status from api_kubernetescluster where (cloud_account_id) = '{account_id}' limit 20""", regions=get.geo_search[0])
            else:                      
                df5 = ApiDB().query_all_regions(query=f"""select cluster_name,id,cluster_type,location,status from api_kubernetescluster where (cloud_account_id) = '{account_id}' limit 20""")
            
            if df5.empty:
                print(bcolors.FAIL + "No Kubernetes clusters found" + bcolors.ENDC)
                exit()
            else:
                html(df5)
                text = "<strong> Kubernetes clusters found:</strong> \n\n"
                txt_html(text)
                print(bcolors.OKBLUE + "We found the next Kubernetes clusters: " + bcolors.ENDC)
                display(df5)
                print(bcolors.OKBLUE + "Status - 0 = Discovered, 1 = Onboarded, 2 = Deleted" + bcolors.ENDC)
                print(bcolors.OKGREEN + "To see search result open: " + bcolors.ENDC + var.file)

    def k8s_conn():
        parser = argparse.ArgumentParser(prog="search_ORG.py", description="Orca App for Support")
        parser.add_argument("-k8s_conn", help="Test k8s connectivity, getting a command to run using <provider_id cluster_name>", nargs=2, metavar=('provider_id', 'cluster_name'))
        parser.add_argument('--geo', nargs=argparse.REMAINDER)
        args = parser.parse_args()

        provider_id_k8s = getattr(args, "k8s_conn")[0]
        cluster_name = getattr(args, "k8s_conn")[1]

        if get.geo_search != None:
            if get.geo_search[0] != 'us' and get.geo_search[0] != 'eu' and get.geo_search[0] != 'ap':
                print(
                    "The argument " + bcolors.FAIL + '--geo' + bcolors.ENDC + " can only be: " + bcolors.FAIL + "us, eu, ap" + bcolors.ENDC)
                exit()
            else:
                df10 = ApiDB().query_all_regions(query=f"""select id from api_cloudaccount where (cloud_provider_id) = '{provider_id_k8s}' limit 20""", regions=get.geo_search[0])
        else:
            df10 = ApiDB().query_all_regions(query=f"""select id from api_cloudaccount where (cloud_provider_id) = '{provider_id_k8s}' limit 20""")

        if df10.empty:
            print(bcolors.FAIL + "No CloudAccount ID Found with provided ID" + bcolors.ENDC)
            exit()
        else:
            account_id = df10['id'][0]
            if get.geo_search != None:
                df5 = ApiDB().query_all_regions(query=f"""select cluster_name,cluster_type,location from api_kubernetescluster where (cloud_account_id) = '{account_id}' limit 20""", regions=get.geo_search[0])
            else:
                df5 = ApiDB().query_all_regions(query=f"""select cluster_name,cluster_type,location from api_kubernetescluster where (cloud_account_id) = '{account_id}' limit 20""")

            if df5.empty:
                print(bcolors.FAIL + "No Kubernetes clusters found" + bcolors.ENDC)
                exit()
            else:
                out = df5.loc[df5['cluster_name'] == cluster_name]
                line = out.index[0]
                cluster_name = out['cluster_name'][line]
                location = out['location'][line]
                cloud_provider_out = out['cluster_type'][line]

                if cloud_provider_out == 'gke':
                    cloud_provider = 'gcp'

                    if get.geo_search != None:
                        df8 = ApiDB().query_all_regions(query=f"""select api_organization.name as "organization_name", api_cloudaccount.name as "Account_Name", api_cloudaccount.cloud_provider_id as "cloud_provider_id", gcp_service_account from api_cloudaccount join api_organization on api_organization.id = api_cloudaccount.organization_id where lower(cloud_provider_id) like '%{provider_id_k8s}%' limit 20""", regions=get.geo_search[0])
                    else:
                        df8 = ApiDB().query_all_regions(query=f"""select api_organization.name as "organization_name", api_cloudaccount.name as "Account_Name", api_cloudaccount.cloud_provider_id as "cloud_provider_id", gcp_service_account from api_cloudaccount join api_organization on api_organization.id = api_cloudaccount.organization_id where lower(cloud_provider_id) like '%{provider_id_k8s}%' limit 20""")
                    
                    SA = df8["gcp_service_account"][0]

                    oname = df8["organization_name"].to_string(index=False)
                    aname = df8["cloud_provider_id"].to_string(index=False)
                    json = get.home_folder + "/.gcp/" + f"{oname}" + "_" + f"{aname}" + ".json"
                    replace_df8 = df8.replace(r"\r+|\n+|\t+", "", regex=True)

                    for i in replace_df8["gcp_service_account"]:
                        f = open(f"{json}", "w")
                        f.write(i[:-1].replace("{ ", "{", 1) + "}")
                        f.close()

                    bashCommand = f"cat '{json}'"
                    process = subprocess.Popen(bashCommand, shell=True, executable="/bin/zsh", stdout=subprocess.PIPE)
                    SA, error = process.communicate()
                    service_account = str(SA).replace("b'", "").replace("\\\\n", "\\n")
                    print(bcolors.OKCYAN + "Please open a new iTerm window and run: " + bcolors.ENDC)
                    print(
                        f"opp {get.orca_folder}/sensors/services/kubernator/local_kubernator.py --cloud-provider {cloud_provider} --cluster-name {cluster_name} gke --gcp-project-id {provider_id_k8s} --gcp-service-account '{service_account}")

                elif cloud_provider_out == 'eks':
                    cloud_provider = 'aws'
                    
                    if get.geo_search != None:
                        df7 = ApiDB().query_all_regions(query=f"""select api_organization.name as "organization_name", api_cloudaccount.name as Account_Name,api_cloudaccount.id as CloudAccount_id,api_cloudaccount.organization_id,api_cloudaccount.aws_role_arn,api_cloudaccount.role_external_id,api_cloudaccount.created_time,api_cloudaccount.status_info from api_cloudaccount join api_organization on api_organization.id = api_cloudaccount.organization_id where (cloud_provider_id) = '{provider_id_k8s}' limit 20""", regions=get.geo_search[0])
                    else:
                        df7 = ApiDB().query_all_regions(query=f"""select api_organization.name as "organization_name", api_cloudaccount.name as Account_Name,api_cloudaccount.id as CloudAccount_id,api_cloudaccount.organization_id,api_cloudaccount.aws_role_arn,api_cloudaccount.role_external_id,api_cloudaccount.created_time,api_cloudaccount.status_info from api_cloudaccount join api_organization on api_organization.id = api_cloudaccount.organization_id where (cloud_provider_id) = '{provider_id_k8s}' limit 20""")
                    
                    aws_role_arn = df7["aws_role_arn"][0]
                    role_external_id = df7["role_external_id"][0]
                    print(bcolors.OKCYAN + "Please open a new iTerm window and run: " + bcolors.ENDC)
                    print("ops")
                    print(
                        bcolors.OKCYAN + "After" + bcolors.FAIL + " ops " + bcolors.ENDC + bcolors.OKCYAN + "is up please run:" + bcolors.ENDC)
                    print(
                        f"AWS_PROFILE=production python {get.orca_folder}/sensors/services/kubernator/local_kubernator.py --cloud-provider {cloud_provider} --cluster-name {cluster_name} eks --aws-region-name {location} --aws-role-arn {aws_role_arn} --aws-role-external-id {role_external_id}")

                elif cloud_provider_out == 'aks':
                    # cloud_provider = 'azure'
                    # df8 = ApiDB().query_all_regions(query=f"""select api_organization.name as "organization_name", api_cloudaccount.name as "Account_Name", api_cloudaccount.cloud_provider_id as "cloud_provider_id", azure_tenant_id, azure_subscription_id from api_cloudaccount join api_organization on api_organization.id = api_cloudaccount.organization_id where lower(cloud_provider_id) like '%{provider_id}%' limit 20""")
                    # tenant_id = df8["azure_tenant_id"][0]
                    # subscription_id = df8["azure_subscription_id"][0]
                    # resource_group = "test"
                    # print(bcolors.OKCYAN + "Please open a new iTerm window and run: " + bcolors.ENDC)
                    # print(f"opp {get.orca_folder}/sensors/services/kubernator/local_kubernator.py --cloud-provider {cloud_provider} --cluster-name {cluster_name} aks ---tenant-id {tenant_id} --subscription-id {subscription_id} --resource-group {resource_group}")
                    print("not supported yet, working on it")

    def prov_id():
        cloudaccount_str = get.provider_id_search[0]

        if get.geo_search != None:
            if get.geo_search[0] != 'us' and get.geo_search[0] != 'eu' and get.geo_search[0] != 'ap':
                print(
                    "The argument " + bcolors.FAIL + '--geo' + bcolors.ENDC + " can only be: " + bcolors.FAIL + "us, eu, ap" + bcolors.ENDC)
                exit()
            else:
                df6 = ApiDB().query_all_regions(query=f"""select api_organization.name as "organization_name", api_cloudaccount.name as Account_Name,api_cloudaccount.id as CloudAccount_id,api_cloudaccount.organization_id,api_cloudaccount.aws_role_arn,api_cloudaccount.role_external_id,api_cloudaccount.created_time,api_cloudaccount.status_info,api_cloudaccount.management_account_id,api_cloudaccount.allowed_regions from api_cloudaccount join api_organization on api_organization.id = api_cloudaccount.organization_id where (cloud_provider_id) = '{cloudaccount_str}' limit 20""", regions=get.geo_search[0])
        else:
            df6 = ApiDB().query_all_regions(query=f"""select api_organization.name as "organization_name", api_cloudaccount.name as Account_Name,api_cloudaccount.id as CloudAccount_id,api_cloudaccount.organization_id,api_cloudaccount.aws_role_arn,api_cloudaccount.role_external_id,api_cloudaccount.created_time,api_cloudaccount.status_info,api_cloudaccount.management_account_id,api_cloudaccount.allowed_regions from api_cloudaccount join api_organization on api_organization.id = api_cloudaccount.organization_id where (cloud_provider_id) = '{cloudaccount_str}' limit 20""")
        
        if df6.empty:
            print(bcolors.FAIL + "No CloudAccount Found with provided ID" + bcolors.ENDC)
            exit()
        else:
            html(df6)
            print(bcolors.OKBLUE + "We found CloudAccount in our search" + bcolors.ENDC)
            display(df6)
            print(bcolors.OKGREEN + "To see search result open: " + bcolors.ENDC + var.file)

    def args_preset():
        preset_str = get.preset_search[0]

        if get.geo_search != None:
            if get.geo_search[0] != 'us' and get.geo_search[0] != 'eu' and get.geo_search[0] != 'ap':
                print(
                    "The argument " + bcolors.FAIL + '--geo' + bcolors.ENDC + " can only be: " + bcolors.FAIL + "us, eu, ap" + bcolors.ENDC)
                exit()
            else:
                df2 = ApiDB().query_all_regions(query=f"""select name,settings from api_accountscansettingspreset where lower(name) like '%{preset_str}%' limit 20""", region=get.geo_search[0])
        else:
            df2 = ApiDB().query_all_regions(query=f"""select name,settings from api_accountscansettingspreset where lower(name) like '%{preset_str}%' limit 20""")
        
        if df2.empty:
            print(bcolors.FAIL + "No Preset Found" + bcolors.ENDC)
            exit()
        else:
            html(df2)
            print(bcolors.OKBLUE + "We found Preset in our search" + bcolors.ENDC)
            display(df2)
            print(bcolors.OKGREEN + "To see search result open: " + bcolors.ENDC + var.file)

    def cloudaccount():
        cloudaccount_id_str = get.cloudaccount_id_search[0]

        if get.geo_search != None:
            if get.geo_search[0] != 'us' and get.geo_search[0] != 'eu' and get.geo_search[0] != 'ap':
                print(
                    "The argument " + bcolors.FAIL + '--geo' + bcolors.ENDC + " can only be: " + bcolors.FAIL + "us, eu, ap" + bcolors.ENDC)
                exit()
            else:
                df10 = ApiDB().query_all_regions(query=f"""select api_organization.name as "organization_name",api_cloudaccount.name,api_cloudaccount.id,api_cloudaccount.cloud_provider_id,api_cloudaccount.created_time from api_cloudaccount join api_organization on api_organization.id = api_cloudaccount.organization_id where (api_cloudaccount.id) = '{cloudaccount_id_str}' limit 20""", regions=get.geo_search[0])
        else:        
            df10 = ApiDB().query_all_regions(query=f"""select api_organization.name as "organization_name",api_cloudaccount.name,api_cloudaccount.id,api_cloudaccount.cloud_provider_id,api_cloudaccount.created_time from api_cloudaccount join api_organization on api_organization.id = api_cloudaccount.organization_id where (api_cloudaccount.id) = '{cloudaccount_id_str}' limit 20""")
        
        if df10.empty:
            print(bcolors.FAIL + "No CloudAccount ID Found with provided ID" + bcolors.ENDC)
            exit()
        else:
            html(df10)
            print(bcolors.OKBLUE + "We found CloudAccount ID in our search" + bcolors.ENDC)
            display(df10)
            print(bcolors.OKGREEN + "To see search result open: " + bcolors.ENDC + var.file)

    def notification():
        notification_search_str = get.notification_search[0]
        if not re.match(r"^[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}$",
                        notification_search_str):
            print(bcolors.FAIL + "UUID is not valid, please verify the ORG id" + bcolors.ENDC)
        
        if get.geo_search != None:
            if get.geo_search[0] != 'us' and get.geo_search[0] != 'eu' and get.geo_search[0] != 'ap':
                print(
                    "The argument " + bcolors.FAIL + '--geo' + bcolors.ENDC + " can only be: " + bcolors.FAIL + "us, eu, ap" + bcolors.ENDC)
                exit()
            else:
                df10 = ApiDB().query_all_regions(query=f"""select api_organization.name as "organization_name",organization_id,data,category,type,create_time,update_time from notifications_notification join api_organization on api_organization.id = notifications_notification.organization_id where (organization_id) = '{notification_search_str}' limit 20""", regions=get.geo_search[0])
        else:        
            df10 = ApiDB().query_all_regions(query=f"""select api_organization.name as "organization_name",organization_id,data,category,type,create_time,update_time from notifications_notification join api_organization on api_organization.id = notifications_notification.organization_id where (organization_id) = '{notification_search_str}' limit 20""")

        if df10.empty:
            print(bcolors.FAIL + "No Notification Found for provided Organization ID" + bcolors.ENDC)
            exit()
        else:
            html(d10)
            print(bcolors.OKBLUE + "We found next Notifications in our search" + bcolors.ENDC)
            display(df10)
            print(bcolors.OKGREEN + "To see search result open: " + bcolors.ENDC + var.file)

    def role():
        role_str = get.role_search[0]
        if get.geo_search != None:
            if get.geo_search[0] != 'us' and get.geo_search[0] != 'eu' and get.geo_search[0] != 'ap':
                print(
                    "The argument " + bcolors.FAIL + '--geo' + bcolors.ENDC + " can only be: " + bcolors.FAIL + "us, eu, ap" + bcolors.ENDC)
                exit()
            df = ApiDB().query_all_regions(query=f"""SELECT rbac_rbacrole.organization_id, rbac_rbacrole.name,rbac_rbacrole.permission_groups,rbac_rbacrole.is_custom FROM rbac_rbacrole WHERE id IN ( SELECT rbac_rbacuseraccess.role_id FROM rbac_rbacuseraccess WHERE apiuser_id IN ( SELECT id FROM api_apiuser WHERE  api_apiuser.original_email like '%{role_str}%')) LIMIT 20""", regions=get.geo_search[0])
        else:
            df = ApiDB().query_all_regions(query=f"""SELECT rbac_rbacrole.organization_id, rbac_rbacrole.name,rbac_rbacrole.permission_groups,rbac_rbacrole.is_custom FROM rbac_rbacrole WHERE id IN ( SELECT rbac_rbacuseraccess.role_id FROM rbac_rbacuseraccess WHERE apiuser_id IN ( SELECT id FROM api_apiuser WHERE  api_apiuser.original_email like '%{role_str}%')) LIMIT 20""")

        if df.empty:
            print(bcolors.FAIL + "No Roles Found" + bcolors.ENDC)
            exit()
        else:
            html(df)
            text = "<strong> The Next Roles found:</strong> \n\n"
            txt_html(text)

            print(bcolors.OKBLUE + "We found Roles in our search" + bcolors.ENDC)
            display(df)
            print(bcolors.OKGREEN + "To see search result open: " + bcolors.ENDC + var.file)

    def user():
        user_str = get.user_search[0]
        if get.geo_search != None:
            if get.geo_search[0] != 'us' and get.geo_search[0] != 'eu' and get.geo_search[0] != 'ap':
                print(
                    "The argument " + bcolors.FAIL + '--geo' + bcolors.ENDC + " can only be: " + bcolors.FAIL + "us, eu, ap" + bcolors.ENDC)
                exit()
            else:
                df3 = ApiDB().query_all_regions(query=f"""select api_apiuser.original_email,api_organization.name as "organization_name",api_apiuser.organization_id,api_apiuser.status from api_apiuser join api_organization on api_organization.id = api_apiuser.organization_id where lower(original_email) like '%{user_str}%' limit 20""", regions=get.geo_search[0])
        else:
            df3 = ApiDB().query_all_regions(query=f"""select api_apiuser.original_email,api_organization.name as "organization_name",api_apiuser.organization_id,api_apiuser.status from api_apiuser join api_organization on api_organization.id = api_apiuser.organization_id where lower(original_email) like '%{user_str}%' limit 20""")
        
        if df3.empty:
            print(bcolors.FAIL + "No User Found" + bcolors.ENDC)
            exit()
        else:
            html(df3)
            print(bcolors.OKBLUE + "We found User in our search" + bcolors.ENDC)
            display(df3)
            print(bcolors.OKGREEN + "To see search result open: " + bcolors.ENDC + var.file)

    def invite():
        invite_str = get.invite_search[0]
        if get.geo_search != None:
            if get.geo_search[0] != 'us' and get.geo_search[0] != 'eu' and get.geo_search[0] != 'ap':
                print(
                    "The argument " + bcolors.FAIL + '--geo' + bcolors.ENDC + " can only be: " + bcolors.FAIL + "us, eu, ap" + bcolors.ENDC)
                exit()
            else:
                df4 = ApiDB().query_all_regions(query=f"""select api_userinvite.email,api_organization.name as "organization_name",api_userinvite.organization_id,api_userinvite.issue_date,'{var.orca_reg_link}' || token || '&email=' || email as invitelink FROM api_userinvite join api_organization on api_organization.id = api_userinvite.organization_id WHERE lower(original_email) like '%{invite_str}%' limit 20""", regions=get.geo_search[0])
        else:
            df4 = ApiDB().query_all_regions(query=f"""select api_userinvite.email,api_organization.name as "organization_name",api_userinvite.organization_id,api_userinvite.issue_date,'{var.orca_reg_link}' || token || '&email=' || email as invitelink FROM api_userinvite join api_organization on api_organization.id = api_userinvite.organization_id WHERE lower(original_email) like '%{invite_str}%' limit 20""")
        
        if df4.empty:
            print(bcolors.FAIL + "No Invite Found" + bcolors.ENDC)
            exit()
        else:
            html(df4)
            print(bcolors.OKBLUE + "We found Invite in our search" + bcolors.ENDC)
            display(df4)
            print(bcolors.OKGREEN + "To see search result open: " + bcolors.ENDC + var.file)

    def aws_conf():
        provider_str = get.provider_id[0]
        if get.geo_search != None:
            if get.geo_search[0] != 'us' and get.geo_search[0] != 'eu' and get.geo_search[0] != 'ap':
                print(
                    "The argument " + bcolors.FAIL + '--geo' + bcolors.ENDC + " can only be: " + bcolors.FAIL + "us, eu, ap" + bcolors.ENDC)
                exit()
            else:
                df7 = ApiDB().query_all_regions(query=f"""select api_organization.name as "organization_name", api_cloudaccount.name as Account_Name,api_cloudaccount.id as CloudAccount_id,api_cloudaccount.organization_id,api_cloudaccount.aws_role_arn,api_cloudaccount.role_external_id,api_cloudaccount.created_time,api_cloudaccount.status_info from api_cloudaccount join api_organization on api_organization.id = api_cloudaccount.organization_id where (cloud_provider_id) = '{provider_str}' limit 20""", regions=get.geo_search[0])
        else:
            df7 = ApiDB().query_all_regions(query=f"""select api_organization.name as "organization_name", api_cloudaccount.name as Account_Name,api_cloudaccount.id as CloudAccount_id,api_cloudaccount.organization_id,api_cloudaccount.aws_role_arn,api_cloudaccount.role_external_id,api_cloudaccount.created_time,api_cloudaccount.status_info from api_cloudaccount join api_organization on api_organization.id = api_cloudaccount.organization_id where (cloud_provider_id) = '{provider_str}' limit 20""")

        org_name_tmp = df7["organization_name"][0]
        org_name = org_name_tmp.replace(' ', '_').lower()
        df8 = ApiDB().query_all_regions(
            query=f"""select scanneraccount_role_arn,scanneraccount_role_external_id from api_organization where lower(name) like '%{org_name}%' limit 20""")


        if df7.empty:
            print(bcolors.FAIL + "No provider ID Found" + bcolors.ENDC)
            exit()
        # rare scenrio in case the same account exist in more then 1 region (we should not have it)
        elif len(df7.index) > 1:
            double = df7["organization_name"][1]

            if double != "":
                aws_role_arn_1 = df7["aws_role_arn"][0]
                role_external_id_1 = df7["role_external_id"][0]
                org_name_1_tmp = df7["organization_name"][0]
                org_name_1 = org_name_1_tmp.replace(' ', '_')
                aws_role_arn_2 = df7["aws_role_arn"][1]
                role_external_id_2 = df7["role_external_id"][1]
                org_name_2_tmp = df7["organization_name"][1]
                org_name_2 = org_name_2_tmp.replace(' ', '_')

                print(
                    f"""{bcolors.OKCYAN}Please Copy the next output to the aws config file in:{bcolors.ENDC} {var.aws_file}

[profile {org_name_1}_{provider_str}]
source_profile = production
role_arn = {aws_role_arn_1}
region = us-east-1
external_id = {role_external_id_1}

[profile {org_name_2}_{provider_str}]
source_profile = production
role_arn = {aws_role_arn_2}
region = us-east-1
external_id = {role_external_id_2}
"""
)

        else:
            aws_role_arn = df7["aws_role_arn"][0]
            role_external_id = df7["role_external_id"][0]
            org_name_tmp = df7["organization_name"][0]
            org_name = org_name_tmp.replace(' ', '_')
            print(
                f"""{bcolors.OKCYAN}Please Copy the next output to the aws config file in:{bcolors.ENDC} {var.aws_file}

[profile {org_name}_{provider_str}]
source_profile = production
role_arn = {aws_role_arn}
region = us-east-1
external_id = {role_external_id}
"""
)

        if not df8.empty:
            org_name_tmp = df7["organization_name"][0]
            org_name = org_name_tmp.replace(' ', '_')
            aws_role_arn = df8["scanneraccount_role_arn"][0]
            role_external_id = df8["scanneraccount_role_external_id"][0]
            print(
                f"""{bcolors.OKCYAN}Please note that we found In-Account Service Account:{bcolors.ENDC}

[profile {org_name}_InAccount_{provider_str}]
source_profile = production
role_arn = {aws_role_arn}
region = us-east-1
external_id = {role_external_id}
"""
)
            
    def gcp_conf():
        gcp_str = get.gcp_id[0]
        
        if get.geo_search != None:
            if get.geo_search[0] != 'us' and get.geo_search[0] != 'eu' and get.geo_search[0] != 'ap':
                print(
                    "The argument " + bcolors.FAIL + '--geo' + bcolors.ENDC + " can only be: " + bcolors.FAIL + "us, eu, ap" + bcolors.ENDC)
                exit()
            else:
                df8 = ApiDB().query_all_regions(query=f"""select api_organization.name as "organization_name", api_cloudaccount.name as "Account_Name", api_cloudaccount.cloud_provider_id as "cloud_provider_id", gcp_service_account from api_cloudaccount join api_organization on api_organization.id = api_cloudaccount.organization_id where lower(cloud_provider_id) like '%{gcp_str}%' limit 20""", regions=get.geo_search[0])
        else:
           df8 = ApiDB().query_all_regions(query=f"""select api_organization.name as "organization_name", api_cloudaccount.name as "Account_Name", api_cloudaccount.cloud_provider_id as "cloud_provider_id", gcp_service_account from api_cloudaccount join api_organization on api_organization.id = api_cloudaccount.organization_id where lower(cloud_provider_id) like '%{gcp_str}%' limit 20""")
        
        if df8.empty:
            print(bcolors.FAIL + "No Data Found" + bcolors.ENDC)
            exit()
        else:
            oname = df8["organization_name"].to_string(index=False)
            aname = df8["cloud_provider_id"].to_string(index=False)
            json = get.home_folder + "/.gcp/" + f"{oname}" + "_" + f"{aname}" + ".json"
            replace_df8 = df8.replace(r"\r+|\n+|\t+", "", regex=True)

            for i in replace_df8["gcp_service_account"]:
                f = open(f"{json}", "w")
                f.write(i[:-1].replace("{ ", "{", 1) + "}")
                f.close()

        bashCommand = f"cat '{json}'| awk " "'{print $15}'" " | rev | cut -c3- | rev | cut -c2-"
        process = subprocess.Popen(bashCommand, shell=True, executable="/bin/zsh", stdout=subprocess.PIPE)
        client_email, error = process.communicate()

        client_email_str = str(client_email).replace("\\n", "").replace("b'", "").replace("'", "")
        print(bcolors.OKBLUE + "We found GCP Project in our search" + bcolors.ENDC)
        print(bcolors.WARNING + json + bcolors.ENDC + bcolors.OKGREEN + " Was created successfully" + bcolors.ENDC)
        print(
            f"""{bcolors.OKCYAN}To active the .json and be able to run gcloud commands
Please open a new iTerm and run next output:{bcolors.ENDC}

gcloud auth activate-service-account --key-file={json}
gcloud config configurations create {aname}
gcloud config set account {client_email_str}
gcloud config set project {aname}
"""
        )

    def res_col():
        parser = argparse.ArgumentParser(prog="search_ORG.py", description="Orca App for Support")
        parser.add_argument("-res_col",help="Provide the next values <provider_id asset_id jwt-token> to create a Reserve Collector",nargs=3, metavar=('provider_id', 'asset_id', 'jwt-token'))
        parser.add_argument('--geo', nargs=argparse.REMAINDER)
        args = parser.parse_args()
        
        provider_id_search = getattr(args, "res_col")[0]
        asset_id_search = getattr(args, "res_col")[1]
        jwt_token_search = getattr(args, "res_col")[2]
        
        if get.geo_search != None:
            if get.geo_search[0] != 'us' and get.geo_search[0] != 'eu' and get.geo_search[0] != 'ap':
                print(
                    "The argument " + bcolors.FAIL + '--geo' + bcolors.ENDC + " can only be: " + bcolors.FAIL + "us, eu, ap" + bcolors.ENDC)
                exit()
            else:
                df9 = ApiDB().query_all_regions(query=f"""select api_organization.name as "organization_name", api_cloudaccount.name as Account_Name,api_cloudaccount.id as "CloudAccount_id",api_cloudaccount.organization_id,api_cloudaccount.aws_role_arn,api_cloudaccount.role_external_id,api_cloudaccount.created_time,api_cloudaccount.status_info from api_cloudaccount join api_organization on api_organization.id = api_cloudaccount.organization_id where (cloud_provider_id) = '{provider_id_search}' limit 20""", regions=get.geo_search[0])
        else:
            df9 = ApiDB().query_all_regions(query=f"""select api_organization.name as "organization_name", api_cloudaccount.name as Account_Name,api_cloudaccount.id as "CloudAccount_id",api_cloudaccount.organization_id,api_cloudaccount.aws_role_arn,api_cloudaccount.role_external_id,api_cloudaccount.created_time,api_cloudaccount.status_info from api_cloudaccount join api_organization on api_organization.id = api_cloudaccount.organization_id where (cloud_provider_id) = '{provider_id_search}' limit 20""")
        
        if df9.empty:
            print(bcolors.FAIL + "No Data Found" + bcolors.ENDC)
            exit()
        else:
            bashCommand = "whoami"
            process = subprocess.Popen(bashCommand, shell=True, executable="/bin/zsh", stdout=subprocess.PIPE)
            login_user, error = process.communicate()
            login_user_str = str(login_user).replace("\\n", "").replace("b'", "").replace("'", "")
            account_id = df9["CloudAccount_id"].to_string(index=False)
            csv(df9)

            df_csv = pd.read_csv(f'{var.csv_file}', skipinitialspace=True)
            location = df_csv.region.to_string(index=False)
            print(bcolors.OKCYAN + "Please open a new iTerm and run next output:" + bcolors.ENDC + "\n")
            print(
                f"prp utils/api_scripts/api.py scan --api-host https://app.{location}.orcasecurity.io --jwt-tokens {jwt_token_search} --customer-account-id {account_id} --assets-to-scan {asset_id_search} --reserve-collectors {login_user_str}_collector_with_vpn --reserve-collector-backconnect-server utils/api_scripts/vpnconnect.json")
            os.remove(var.csv_file)
            exit()

    def res_s3():
        parser = argparse.ArgumentParser(prog="search_ORG.py", description="Orca App for Support")
        parser.add_argument("-res_s3", help="Provide the next values <provider_id bucket_name jwt-token> to create a S3 Bucket Reserve Collector", nargs=3, metavar=('provider_id', 'bucket_name', 'jwt-token'))
        parser.add_argument('--geo', nargs=argparse.REMAINDER)
        args = parser.parse_args()
        
        provider_id_search = getattr(args, "res_s3")[0]
        bucket_name_search = getattr(args, "res_s3")[1]
        jwt_token_search = getattr(args, "res_s3")[2]

        if get.geo_search != None:
            if get.geo_search[0] != 'us' and get.geo_search[0] != 'eu' and get.geo_search[0] != 'ap':
                print(
                    "The argument " + bcolors.FAIL + '--geo' + bcolors.ENDC + " can only be: " + bcolors.FAIL + "us, eu, ap" + bcolors.ENDC)
                exit()
            else:
                df9 = ApiDB().query_all_regions(query=f"""select api_organization.name as "organization_name", api_cloudaccount.name as Account_Name,api_cloudaccount.id as "CloudAccount_id",api_cloudaccount.organization_id,api_cloudaccount.aws_role_arn,api_cloudaccount.role_external_id,api_cloudaccount.created_time,api_cloudaccount.status_info from api_cloudaccount join api_organization on api_organization.id = api_cloudaccount.organization_id where (cloud_provider_id) = '{provider_id_search}' limit 20""", regions=get.geo_search[0])
        else:
            df9 = ApiDB().query_all_regions(query=f"""select api_organization.name as "organization_name", api_cloudaccount.name as Account_Name,api_cloudaccount.id as "CloudAccount_id",api_cloudaccount.organization_id,api_cloudaccount.aws_role_arn,api_cloudaccount.role_external_id,api_cloudaccount.created_time,api_cloudaccount.status_info from api_cloudaccount join api_organization on api_organization.id = api_cloudaccount.organization_id where (cloud_provider_id) = '{provider_id_search}' limit 20""")

        if df9.empty:
            print(bcolors.FAIL + "No Data Found" + bcolors.ENDC)
            exit()
        else:
            bashCommand = "whoami"
            process = subprocess.Popen(bashCommand, shell=True, executable="/bin/zsh", stdout=subprocess.PIPE)
            login_user, error = process.communicate()
            login_user_str = str(login_user).replace("\\n", "").replace("b'", "").replace("'", "")
            account_id = df9["CloudAccount_id"].to_string(index=False)
            csv(df9)

            df_csv = pd.read_csv(f'{var.csv_file}', skipinitialspace=True)
            location = df_csv.region.to_string(index=False)
            print(bcolors.OKCYAN + "Please open a new iTerm and run next output:" + bcolors.ENDC + "\n")
            print(
                f"prp utils/api_scripts/api.py scan --api-host https://app.{location}.orcasecurity.io --jwt-tokens {jwt_token_search} --customer-account-id {account_id} --buckets-to-scan {bucket_name_search} --reserve-s3-collectors {login_user_str}_collector_with_vpn --reserve-collector-backconnect-server utils/api_scripts/vpnconnect.json")
            os.remove(var.csv_file)
            exit()

    def res_fargate():
        parser = argparse.ArgumentParser(prog="search_ORG.py", description="Orca App for Support")
        parser.add_argument("-res_fargate", help="Provide the next values <provider_id fargate_asset_id jwt-token> to create a Fargate Cluster Reserve Collector", nargs=3, metavar=('provider_id', 'fargate_asset_id', 'jwt-token'))
        parser.add_argument('--geo', nargs=argparse.REMAINDER)
        args = parser.parse_args()
        provider_id_search = getattr(args, "res_fargate")[0]
        fargate_asset_id_search = getattr(args, "res_fargate")[1]
        jwt_token_search = getattr(args, "res_fargate")[2]

        if get.geo_search != None:
            if get.geo_search[0] != 'us' and get.geo_search[0] != 'eu' and get.geo_search[0] != 'ap':
                print(
                    "The argument " + bcolors.FAIL + '--geo' + bcolors.ENDC + " can only be: " + bcolors.FAIL + "us, eu, ap" + bcolors.ENDC)
                exit()
            else:
                df9 = ApiDB().query_all_regions(query=f"""select api_organization.name as "organization_name", api_cloudaccount.name as Account_Name,api_cloudaccount.id as "CloudAccount_id",api_cloudaccount.organization_id,api_cloudaccount.aws_role_arn,api_cloudaccount.role_external_id,api_cloudaccount.created_time,api_cloudaccount.status_info from api_cloudaccount join api_organization on api_organization.id = api_cloudaccount.organization_id where (cloud_provider_id) = '{provider_id_search}' limit 20""", regions=get.geo_search[0])
        else:
            df9 = ApiDB().query_all_regions(query=f"""select api_organization.name as "organization_name", api_cloudaccount.name as Account_Name,api_cloudaccount.id as "CloudAccount_id",api_cloudaccount.organization_id,api_cloudaccount.aws_role_arn,api_cloudaccount.role_external_id,api_cloudaccount.created_time,api_cloudaccount.status_info from api_cloudaccount join api_organization on api_organization.id = api_cloudaccount.organization_id where (cloud_provider_id) = '{provider_id_search}' limit 20""")
        
        if df9.empty:
            print(bcolors.FAIL + "No Data Found" + bcolors.ENDC)
            exit()
        else:
            bashCommand = "whoami"
            process = subprocess.Popen(bashCommand, shell=True, executable="/bin/zsh", stdout=subprocess.PIPE)
            login_user, error = process.communicate()
            login_user_str = str(login_user).replace("\\n", "").replace("b'", "").replace("'", "")
            account_id = df9["CloudAccount_id"].to_string(index=False)
            csv(df9)

            df_csv = pd.read_csv(f'{var.csv_file}', skipinitialspace=True)
            location = df_csv.region.to_string(index=False)
            print(bcolors.OKCYAN + "Please open a new iTerm and run next output:" + bcolors.ENDC + "\n")
            print(
                f"prp utils/api_scripts/api.py scan --api-host https://app.{location}.orcasecurity.io --jwt-tokens {jwt_token_search} --customer-account-id {account_id} --assets-to-scan {fargate_asset_id_search} --reserve-fargate-collectors {login_user_str}_collector_with_vpn --reserve-collector-backconnect-server utils/api_scripts/vpnconnect.json")
            os.remove(var.csv_file)
            exit()

    def allow_reg():
        profile_str = get.profile_search[0]

        bashCommand = f"cat /Users/kobykagan/.aws/config | grep -w 'profile {profile_str}'"
        process = subprocess.Popen(bashCommand, shell=True, executable="/bin/zsh", stdout=subprocess.PIPE)
        result, error = process.communicate()

        if len(result) == 0:
            print(f"No Profile with the name {profile_str}")
            exit()
        else:
            pass

        regions = ['us-east-2', 'us-east-1', 'us-west-2', 'us-west-1', 'sa-east-1', 'eu-west-3', 'eu-west-2', 'eu-west-1', 'eu-north-1', 'eu-central-1', 'ca-central-1', 'ap-southeast-2', 'ap-southeast-1', 'ap-south-1', 'ap-northeast-3', 'ap-northeast-2', 'ap-northeast-1', 'sa-east-1']
        a_reg = []

        for reg in regions:
            ec2 = boto3.session.Session(profile_name=profile_str, region_name=reg).client(service_name='ec2')
            try:
                ec2.describe_regions()
                a_reg.append(reg)
            except:
                pass

        if regions == a_reg: 
            print("All Regions allowed")
        else:
            print(f"Allowed Regions: {a_reg}")

def config_bastion():
    bastion = subprocess.Popen("ls -l ~/.ssh | grep config_bastion", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, err = bastion.communicate()
    search = "config_bastion".encode()
    if search in out:
        pass
    else:
        new_bastion = subprocess.Popen("cd ~/.ssh; ln -s $SRC_ROOT/cli/op/shell_rc/ssh/config_bastion config_bastion", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        include_bastion = subprocess.Popen("echo 'Include ~/.ssh/config_bastion' > ~/.ssh/config", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

def get_val(path):
    with open(path) as f:
        return json.load(f)

def aws_connect():
    awd_connect = subprocess.Popen("aws sqs list-queues", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, err = awd_connect.communicate()
    token = "SSO".encode()
    if token in out:
        open_tunnel = subprocess.Popen("aws sso login", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT).wait()

def tunnel():
    config_bastion()

    #configure max time for Tunnels to be opened
    max_time = "08:00:00"
    max_len = 9

    # check if tunnels are opened in case tunnels are open more then max_time, the tunnel will be reset
    # checking US tunnel
    need_tunnel_9000 = subprocess.Popen("netstat -an | grep 9000", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    need_tunnel_out, err = need_tunnel_9000.communicate()
    need = "127.0.0.1.9000".encode()
    # if Tunnel open
    if need in need_tunnel_out:
        get_pid_tun_1 = subprocess.Popen(
            "lsof -i :9000 | grep 'localhost:cslistener (LISTEN)' | grep -v 'PID' | awk '{print $2; exit}'", shell=True,
            executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out_1, err = get_pid_tun_1.communicate()
        pid_1_str = out_1.decode()
        pid_1 = pid_1_str[:-1]
        time_tun_1 = subprocess.Popen(f"ps -o etime {pid_1} | grep -v 'ELAPSED'", shell=True, executable="/bin/zsh",
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out_time_1, err = time_tun_1.communicate()
        out_time_1_str = out_time_1.decode()

        time_pid_1 = out_time_1_str[:-1]
        # if found open more then max_time, reset tunnel
        if time_pid_1 > max_time or len(time_pid_1) >= max_len:
            kill_pid_1 = subprocess.Popen(f"kill -9 {pid_1}", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out_pid_1, err = kill_pid_1.communicate()
            main_tunnel = subprocess.Popen("aws_rds_tunnel production 9000", shell=True, executable="/bin/zsh",
                                           stdout=subprocess.PIPE)
            search_val = "localhost:9000".encode()
            for line in main_tunnel.stdout:
                if search_val in line:
                    print(bcolors.OKBLUE + "Established tunnel to production environment US" + bcolors.ENDC)
                    time.sleep(1)
                    break

    else:
        main_tunnel = subprocess.Popen("aws_rds_tunnel production 9000", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE)
        search_val = "localhost:9000".encode()
        for line in main_tunnel.stdout:
            if search_val in line:
                print(bcolors.OKBLUE + "Established tunnel to production environment US" + bcolors.ENDC)
                time.sleep(1)
                break

    need_tunnel_9001 = subprocess.Popen("netstat -an | grep 9001", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    need_tunnel_out, err = need_tunnel_9001.communicate()
    need = "127.0.0.1.9001".encode()
    if need in need_tunnel_out:
        get_pid_tun_2 = subprocess.Popen("lsof -i :9001 | grep 'localhost:etlservicemgr (LISTEN)' | grep -v 'PID' | awk '{print $2; exit}'", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out_2, err = get_pid_tun_2.communicate()
        pid_2_str = out_2.decode()
        pid_2 = pid_2_str[:-1]
        time_tun_2 = subprocess.Popen(f"ps -o etime {pid_2} | grep -v 'ELAPSED'", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out_time_2, err = time_tun_2.communicate()
        out_time_2_str = out_time_2.decode()

        time_pid_2 = out_time_2_str[:-1]
        if time_pid_2 > max_time or len(time_pid_2) >= max_len:
            kill_pid_2 = subprocess.Popen(f"kill -9 {pid_2}", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out_pid_2, err = kill_pid_2.communicate()
            eu_tunnel = subprocess.Popen("aws_rds_tunnel production 9001 --region eu-central-1", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE)
            search_val = "localhost:9001".encode()
            for line in eu_tunnel.stdout:
                if search_val in line:
                    print(bcolors.OKBLUE + "Established tunnel to production environment EU" + bcolors.ENDC)
                    time.sleep(1)
                    break
    else:
        eu_tunnel = subprocess.Popen("aws_rds_tunnel production 9001 --region eu-central-1", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE)
        search_val = "localhost:9001".encode()
        for line in eu_tunnel.stdout:
            if search_val in line:
                print(bcolors.OKBLUE + "Established tunnel to production environment EU" + bcolors.ENDC)
                time.sleep(1)
                break

    need_tunnel_9002 = subprocess.Popen("lsof -i :9002", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    need_tunnel_out, err = need_tunnel_9002.communicate()
    need = "localhost:dynamid (LISTEN)".encode()
    if need in need_tunnel_out:
        get_pid_tun_3 = subprocess.Popen(
            "lsof -i :9002 | grep 'localhost:dynamid (LISTEN)' | grep -v 'PID' | awk '{print $2; exit}'", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out_3, err = get_pid_tun_3.communicate()
        pid_3_str = out_3.decode()
        pid_3 = pid_3_str[:-1]
        time_tun_3 = subprocess.Popen(f"ps -o etime {pid_3} | grep -v 'ELAPSED'", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out_time_3, err = time_tun_3.communicate()
        out_time_3_str = out_time_3.decode()
        time_pid_3 = out_time_3_str[:-1]

        if time_pid_3 > max_time or len(time_pid_3) >= max_len:
            kill_pid_3 = subprocess.Popen(f"kill -9 {pid_3}", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out_pid_3, err = kill_pid_3.communicate()
            ap_tunnel = subprocess.Popen("aws_rds_tunnel production 9002 --region ap-southeast-2", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE)
            search_val = "localhost:9002".encode()
            for line in ap_tunnel.stdout:
                if search_val in line:
                    print(bcolors.OKBLUE + "Established tunnel to production environment AU" + bcolors.ENDC + "\n")
                    time.sleep(1)
                    break
    else:
        ap_tunnel = subprocess.Popen("aws_rds_tunnel production 9002 --region ap-southeast-2", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE)
        search_val = "localhost:9002".encode()
        for line in ap_tunnel.stdout:
            if search_val in line:
                print(bcolors.OKBLUE + "Established tunnel to production environment AU" + bcolors.ENDC + "\n")
                time.sleep(1)
                break

    confirm_tunel()

def confirm_tunel():
    # make sure all tunnels are up and running
    need_tunnel_9000 = subprocess.Popen("lsof -i :9000", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT)
    need_tunnel_out, err = need_tunnel_9000.communicate()
    need = "localhost:cslistener (LISTEN)".encode()
    while need not in need_tunnel_out:
        need_tunnel_9000 = subprocess.Popen("lsof -i :9000", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE,
                                            stderr=subprocess.STDOUT)
        need_tunnel_out, err = need_tunnel_9000.communicate()
        time.sleep(1)

    need_tunnel_9001 = subprocess.Popen("lsof -i :9001", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT)
    need_tunnel_out, err = need_tunnel_9001.communicate()
    need = "localhost:etlservicemgr (LISTEN)".encode()
    while need not in need_tunnel_out:
        need_tunnel_9001 = subprocess.Popen("lsof -i :9001", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE,
                                            stderr=subprocess.STDOUT)
        need_tunnel_out, err = need_tunnel_9001.communicate()
        time.sleep(1)

    need_tunnel_9002 = subprocess.Popen("lsof -i :9002", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT)
    need_tunnel_out, err = need_tunnel_9002.communicate()
    need = "localhost:dynamid (LISTEN)".encode()
    while need not in need_tunnel_out:
        need_tunnel_9002 = subprocess.Popen("lsof -i :9002", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE,
                                            stderr=subprocess.STDOUT)
        need_tunnel_out, err = need_tunnel_9002.communicate()
        time.sleep(1)

def garbage():
    if os.path.exists(var.file):
        os.remove(var.file)
        fle = Path(f"{var.file}")
        fle.touch(exist_ok=True)

    if os.path.exists(var.csv_file):
        os.remove(var.csv_file)
        fle = Path(f"{var.csv_file}")
        fle.touch(exist_ok=True)

def html(df):
    html = df.to_html()
    text_file = open(f"{var.file}", "a+")
    text_file.write(html)
    text_file.close()

def csv(df):
    csv_out = df.to_csv()
    text_file = open(f"{var.csv_file}", "a+")
    text_file.write(csv_out)
    text_file.close()

def txt_html_end(text):
    text = text
    soup = BeautifulSoup(text, "html.parser")

    with open(var.file, "a", encoding='utf-8') as file:
        # prettify the soup object and convert it into a string
        file.write(str(soup.prettify()))

def txt_html(text):
    text = text
    soup = BeautifulSoup(text, "html.parser")

    with open(var.file, "r+", encoding='utf-8') as file:
        # prettify the soup object and convert it into a string
        content = file.read()
        file.seek(0, 0)
        file.write(str(soup.prettify()) + content)

if __name__ == "__main__":
    # remove Future Warning text - remove in case need to debug
    #sys.tracebacklimit = 0

    garbage()
    
    if get.args.allow_reg:
        options.allow_reg()
        
    if get.args.org_name:
        options.org_name()

    if get.args.org_id:
        options.org_id()

    if get.args.k8s:
        options.k8s()
        
    if get.args.k8s_conn:
        options.k8s_conn()
        
    if get.args.prov_id:
        options.prov_id()

    if get.args.preset:
        options.args_preset()

    if get.args.cloudaccount:
        options.cloudaccount()

    if get.args.notification:
        options.notification()

    if get.args.role:
        options.role()

    if get.args.user:
        options.user()

    if get.args.invite:
        options.invite()

    if get.args.aws_conf:
        options.aws_conf()

    if get.args.gcp_conf:
        options.gcp_conf()

    if get.args.res_col:
        options.res_col()

    if get.args.res_s3:
        options.res_s3()

    if get.args.res_fargate:
        options.res_fargate()
