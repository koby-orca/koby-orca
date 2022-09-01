import pandas as pd
import psycopg2, argparse, os, subprocess, json,csv,time,sys,re
from IPython.display import display
from pathlib import Path
from subprocess import check_output
import warnings

#remove FutureWarrning text
warnings.filterwarnings('ignore')

home_folder = os.environ.get("HOME")

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

    # check if tunnels are opened in case tunnels are open more then max_time, the tunnel will be reset

    need_tunnel_9000 = subprocess.Popen("netstat -an | grep 9000", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    need_tunnel_out, err = need_tunnel_9000.communicate()
    need = "127.0.0.1.9000".encode()
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
        if time_pid_1 > max_time:
            kill_pid_1 = subprocess.Popen(f"kill -9 {pid_1}", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out_pid_1, err = kill_pid_1.communicate()
            main_tunnel = subprocess.Popen("aws_rds_tunnel production 9000", shell=True, executable="/bin/zsh",
                                           stdout=subprocess.PIPE)
            search_val = "localhost:9000".encode()
            for line in main_tunnel.stdout:
                if search_val in line:
                    print(bcolors.OKBLUE + "Established tunnel to production environment US" + bcolors.ENDC)
                    break
        else:
            pass
    else:
        main_tunnel = subprocess.Popen("aws_rds_tunnel production 9000", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE)
        search_val = "localhost:9000".encode()
        for line in main_tunnel.stdout:
            if search_val in line:
                print(bcolors.OKBLUE + "Established tunnel to production environment US" + bcolors.ENDC)
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
        if time_pid_2 > max_time:
            kill_pid_2 = subprocess.Popen(f"kill -9 {pid_2}", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out_pid_2, err = kill_pid_2.communicate()
            eu_tunnel = subprocess.Popen("aws_rds_tunnel production 9001 --region eu-central-1", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE)
            search_val = "localhost:9001".encode()
            for line in eu_tunnel.stdout:
                if search_val in line:
                    print(bcolors.OKBLUE + "Established tunnel to production environment EU" + bcolors.ENDC)
                    break
    else:
        eu_tunnel = subprocess.Popen("aws_rds_tunnel production 9001 --region eu-central-1", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE)
        search_val = "localhost:9001".encode()
        for line in eu_tunnel.stdout:
            if search_val in line:
                print(bcolors.OKBLUE + "Established tunnel to production environment EU" + bcolors.ENDC)
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
        if time_pid_3 > max_time:
            kill_pid_3 = subprocess.Popen(f"kill -9 {pid_3}", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out_pid_3, err = kill_pid_3.communicate()
            ap_tunnel = subprocess.Popen("aws_rds_tunnel production 9002 --region ap-southeast-2", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE)
            search_val = "localhost:9002".encode()
            for line in ap_tunnel.stdout:
                if search_val in line:
                    print(bcolors.OKBLUE + "Established tunnel to production environment AU" + bcolors.ENDC + "\n")
                    break
    else:
        ap_tunnel = subprocess.Popen("aws_rds_tunnel production 9002 --region ap-southeast-2", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE) 
        search_val = "localhost:9002".encode()
        for line in ap_tunnel.stdout:
            if search_val in line:
                print(bcolors.OKBLUE + "Established tunnel to production environment AU" + bcolors.ENDC + "\n")
                break

        # make sure all tunnels are up and running 
        need_tunnel_9000 = subprocess.Popen("lsof -i :9000", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        need_tunnel_out, err = need_tunnel_9000.communicate()
        need = "localhost:cslistener (LISTEN)".encode()
        while need not in need_tunnel_out:
            need_tunnel_9000 = subprocess.Popen("lsof -i :9000", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            need_tunnel_out, err = need_tunnel_9000.communicate()
            time.sleep(1)
    
        need_tunnel_9001 = subprocess.Popen("lsof -i :9001", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        need_tunnel_out, err = need_tunnel_9001.communicate()
        need = "localhost:etlservicemgr (LISTEN)".encode()
        while need not in need_tunnel_out:
            need_tunnel_9001 = subprocess.Popen("lsof -i :9001", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            need_tunnel_out, err = need_tunnel_9001.communicate()
            time.sleep(1)
    
        need_tunnel_9002 = subprocess.Popen("lsof -i :9002", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        need_tunnel_out, err = need_tunnel_9002.communicate()
        need = "localhost:dynamid (LISTEN)".encode()
        while need not in need_tunnel_out:
            need_tunnel_9002 = subprocess.Popen("lsof -i :9002", shell=True, executable="/bin/zsh", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            need_tunnel_out, err = need_tunnel_9002.communicate()
            time.sleep(1)


class ApiDB:

    def query_api_db(self, query, port):
        vals = get_val(home_folder+"/.secret/secrets.json")
        user = vals['user'] 
        password = vals['password']
        
        database = "postgres"
        user = user
        password = password
        host = "localhost"
        conn = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)
        df = pd.read_sql(con=conn, sql=query)
        pd.set_option("display.max_colwidth", 100)
        return df

    def query_api_db_ap(self, query, port):
        vals = get_val(home_folder+"/.secret/secrets.json")
        user = vals['user'] 
        password = vals['password']
        
        database = "orca"
        user = user
        password = password
        host = "localhost"
        conn = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)
        df = pd.read_sql(con=conn, sql=query)
        pd.set_option("display.max_colwidth", 199)
        return df

    def query_all_regions(self, query, regions="all"):
        aws_connect()
        tunnel()
          
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
                df["region"] = "us"
            elif port == 9001:
                df = self.query_api_db(query, port=port)
                df["region"] = "eu"
            elif port == 9002:
                df = self.query_api_db_ap(query, port=port)
                df["region"] = "ap"
            ret = pd.concat([ret, df], ignore_index=True)
        return ret


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(prog="search_ORG.py", description="Orca App for Support")
    # set arguments
    parser.add_argument("-org_name", help="org_name will search for the Organization by Name in DB", nargs=1, metavar=('organization_name'))
    parser.add_argument("-org_id", help="org_id will search for the Organization by ID in DB, must use the full organization ID", nargs=1, metavar=('organization_id'))
    parser.add_argument("-prov_id", help="prov_id will search for the Account by ID in DB, must use the full provider ID/Project Name", nargs=1, metavar=('provider_id'))
    parser.add_argument("-cloudaccount", help="Find the CloudAccount via the Orca cloudaccount_id", nargs=1, metavar=('cloudaccount_id'))
    parser.add_argument("-user", help="user will search for any User in DB", nargs=1, metavar=('email_address'))
    parser.add_argument("-preset", help="preset will search any Preset in DB", nargs=1, metavar=('org_name'))
    parser.add_argument("-invite", help="invite will search any Invite with a specific email in DB", nargs=1, metavar=('email_address'))
    parser.add_argument("-aws_conf", help="Provide aws_config data using the provider ID, in order to use aws cli", nargs=1, metavar=('provider_id'))
    parser.add_argument("-gcp_conf", help="Provide gcp_config data using the GCP Project name, in order to use gcloud cli", nargs=1, metavar=('provider_id'))
    parser.add_argument("-res_col", help="Provide the next values <provider_id asset_id jwt-token> to create a Reserve Collector", nargs=3, metavar=('provider_id','asset_id','jwt-token'))
    parser.add_argument("-res_s3", help="Provide the next values <provider_id bucket_name jwt-token> to create a S3 Bucket Reserve Collector", nargs=3, metavar=('provider_id','bucket_name','jwt-token'))
    parser.add_argument("-res_fargate", help="Provide the next values <provider_id fargate_asset_id jwt-token> to create a Fargate Cluster Reserve Collector", nargs=3, metavar=('provider_id', 'fargate_asset_id', 'jwt-token'))

    # arguments to variables 
    args = parser.parse_args()
    orgName_search = getattr(args, "org_name")
    orgID_search = getattr(args, "org_id")
    preset_search = getattr(args, "preset")
    user_search = getattr(args, "user")
    invite_search = getattr(args, "invite")
    provider_id_search = getattr(args, "prov_id")
    provider_id = getattr(args, "aws_conf")
    gcp_id = getattr(args, "gcp_conf")
    cloudaccount_id_search = getattr(args, "cloudaccount")


    # global variables
    file = home_folder + "/Desktop/Search.html"
    aws_file = home_folder + "/.aws/config"
    orca_reg_link = "https://app.orcasecurity.io/register?invite_code="
    csv_file = home_folder + "/Desktop/Search.csv"

    # remove old Search.html Search.csv files 
    if os.path.exists(file):
        os.remove(file)
        fle = Path(f"{file}")
        fle.touch(exist_ok=True)

    if os.path.exists(csv_file):
        os.remove(csv_file)
        fle = Path(f"{csv_file}")
        fle.touch(exist_ok=True)

    if args.org_name:
        orgName_str = orgName_search[0]
        df = ApiDB().query_all_regions(
            query=f"""select name,id,customer_type from api_organization where lower(name) like '%{orgName_str}%' limit 20"""
        )
        if df.empty:
            print(bcolors.FAIL + "No Organization Found" + bcolors.ENDC)
            exit()
        else:
            html = df.to_html()
            text_file = open(f"{file}", "a+")
            text_file.write(html)
            text_file.close()
            print(bcolors.OKBLUE + "We found Organization in our search" + bcolors.ENDC)
            display(df)
            print(bcolors.OKGREEN + "To see search result open: " + bcolors.ENDC + file)

    if args.org_id:
        tunnel()
        orgID_str = orgID_search[0]
        # confirm orgID_str is per UUID example - 7c9ee3e1-bbea-447f-853c-c53b9b190240
        if not re.match(r"^[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}$",orgID_str):
            print(bcolors.FAIL + "UUID is not valid, please verify the ORG id"+ bcolors.ENDC)
        else:
            df5 = ApiDB().query_all_regions(
                query=f"""select name,id,customer_type from api_organization where (id) = '{orgID_str}' limit 20"""
            )
            if df5.empty:
                print(bcolors.FAIL + "No Organization Found with provided ID" + bcolors.ENDC)
                exit()
            else:
                html = df5.to_html()
                text_file = open(f"{file}", "a+")
                text_file.write(html)
                text_file.close()
                print(bcolors.OKBLUE + "We found Organization in our search" + bcolors.ENDC)
                display(df5)
                print(bcolors.OKGREEN + "To see search result open: " + bcolors.ENDC + file)

    if args.prov_id:
        cloudaccount_str = provider_id_search[0]
        df6 = ApiDB().query_all_regions(query=f"""select api_organization.name as "Org_Name", api_cloudaccount.name as Account_Name,api_cloudaccount.id as CloudAccount_id,api_cloudaccount.organization_id,api_cloudaccount.aws_role_arn,api_cloudaccount.role_external_id,api_cloudaccount.created_time,api_cloudaccount.status_info,api_cloudaccount.management_account_id,api_cloudaccount.allowed_regions from api_cloudaccount join api_organization on api_organization.id = api_cloudaccount.organization_id where (cloud_provider_id) = '{cloudaccount_str}' limit 20"""
        )
        if df6.empty:
            print(bcolors.FAIL + "No CloudAccount Found with provided ID" + bcolors.ENDC)
            exit()
        else:
            html = df6.to_html()
            text_file = open(f"{file}", "a+")
            text_file.write(html)
            text_file.close()
            print(bcolors.OKBLUE + "We found CloudAccount in our search" + bcolors.ENDC)
            display(df6)
            print(bcolors.OKGREEN + "To see search result open: " + bcolors.ENDC + file)

    if args.preset:
        preset_str = preset_search[0]
        df2 = ApiDB().query_all_regions(
            query=f"""select name,settings from api_accountscansettingspreset where lower(name) like '%{preset_str}%' limit 20"""
        )
        if df2.empty:
            print(bcolors.FAIL + "No Preset Found" + bcolors.ENDC)
            exit()
        else:
            html = df2.to_html()
            text_file = open(f"{file}", "a+")
            text_file.write(html)
            text_file.close()
            print(bcolors.OKBLUE + "We found Preset in our search" + bcolors.ENDC)
            display(df2)
            print(bcolors.OKGREEN + "To see search result open: " + bcolors.ENDC + file)           

    if args.cloudaccount:
        cloudaccount_id_str = cloudaccount_id_search[0]
        df10 = ApiDB().query_all_regions(
            query=f"""select name,id,cloud_provider_id,created_time from api_cloudaccount where (id) = '{cloudaccount_id_str}' limit 20"""
        )
        if df10.empty:
            print(bcolors.FAIL + "No CloudAccount ID Found with provided ID" + bcolors.ENDC)
            exit()
        else:
            html = df10.to_html()
            text_file = open(f"{file}", "a+")
            text_file.write(html)
            text_file.close()
            print(bcolors.OKBLUE + "We found CloudAccount ID in our search" + bcolors.ENDC)
            display(df10)
            print(bcolors.OKGREEN + "To see search result open: " + bcolors.ENDC + file)

    if args.user:
        user_str = user_search[0]
        df3 = ApiDB().query_all_regions(
            query=f"""select original_email,organization_id,status from api_apiuser where lower(original_email) like '%{user_str}%' limit 20"""
        )
        if df3.empty:
            print(bcolors.FAIL + "No User Found" + bcolors.ENDC)
            exit()
        else:
            html = df3.to_html()
            text_file = open(f"{file}", "a+")
            text_file.write(html)
            text_file.close()
            print(bcolors.OKBLUE + "We found User in our search" + bcolors.ENDC)
            display(df3)
            print(bcolors.OKGREEN + "To see search result open: " + bcolors.ENDC + file)

    if args.invite:
        tunnel()
        invite_str = invite_search[0]
        df4 = ApiDB().query_all_regions(
            query=f"""select email,organization_id,issue_date,'{orca_reg_link}' || token || '&email=' || email as invitelink FROM api_userinvite WHERE lower(original_email) like '%{invite_str}%' limit 20"""
        )
        if df4.empty:
            print(bcolors.FAIL + "No Invite Found" + bcolors.ENDC)
            exit()
        else:
            html = df4.to_html()
            text_file = open(f"{file}", "a+")
            text_file.write(html)
            text_file.close()
            print(bcolors.OKBLUE + "We found Invite in our search" + bcolors.ENDC)
            display(df4)
            print(bcolors.OKGREEN + "To see search result open: " + bcolors.ENDC + file)

    if args.aws_conf:
        provider_str = provider_id[0]
        df7 = ApiDB().query_all_regions(
            query=f"""select api_organization.name as "Org_Name", api_cloudaccount.name as Account_Name,api_cloudaccount.id as CloudAccount_id,api_cloudaccount.organization_id,api_cloudaccount.aws_role_arn,api_cloudaccount.role_external_id,api_cloudaccount.created_time,api_cloudaccount.status_info from api_cloudaccount join api_organization on api_organization.id = api_cloudaccount.organization_id where (cloud_provider_id) = '{provider_str}' limit 20"""
        )
        if df7.empty:
            print(bcolors.FAIL + "No provider ID Found" + bcolors.ENDC)
            exit()
        # rare scenrio in case the same account exist in more then 1 region (we should not have it)
        elif len(df7.index) > 1:
            double = df7["Org_Name"][1]

            if double != "":
                aws_role_arn_1 = df7["aws_role_arn"][0]
                role_external_id_1 = df7["role_external_id"][0]
                org_name_1 = df7["Org_Name"][0]
                aws_role_arn_2 = df7["aws_role_arn"][1]
                role_external_id_2 = df7["role_external_id"][1]
                org_name_2 = df7["Org_Name"][1]

                print(
                    f"""{bcolors.OKCYAN}Please Copy the next output to the aws config file in:{bcolors.ENDC} {aws_file}

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
            org_name = df7["Org_Name"][0]
            print(
                f"""{bcolors.OKCYAN}Please Copy the next output to the aws config file in:{bcolors.ENDC} {aws_file}

[profile {org_name}_{provider_str}]
source_profile = production
role_arn = {aws_role_arn}
region = us-east-1
external_id = {role_external_id}
"""
)

    if args.gcp_conf:
        gcp_str = gcp_id[0]
        df8 = ApiDB().query_all_regions(
            query=f"""select api_organization.name as "Org_Name", api_cloudaccount.name as "Account_Name", api_cloudaccount.cloud_provider_id as "cloud_provider_id", gcp_service_account from api_cloudaccount join api_organization on api_organization.id = api_cloudaccount.organization_id where lower(cloud_provider_id) like '%{gcp_str}%' limit 20"""
        )
        if df8.empty:
            print(bcolors.FAIL + "No Data Found" + bcolors.ENDC)
            exit()
        else:
            oname = df8["Org_Name"].to_string(index=False)
            aname = df8["cloud_provider_id"].to_string(index=False)
            json = home_folder + "/.gcp/" + f"{oname}" + "_" + f"{aname}" + ".json"
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
            f"""
{bcolors.OKCYAN}To active the .json and be able to run gcloud commands
Please open a new iTerm and run next output:{bcolors.ENDC}

gcloud auth activate-service-account --key-file={json}
gcloud config configurations create {aname}
gcloud config set account {client_email_str}
gcloud config set project {aname}
"""
)

    if args.res_col:
        provider_id_search = getattr(args, "res_col")[0]
        asset_id_search = getattr(args, "res_col")[1]
        jwt_token_search = getattr(args, "res_col")[2]
        
        df9 = ApiDB().query_all_regions(query=f"""select api_organization.name as "Org_Name", api_cloudaccount.name as Account_Name,api_cloudaccount.id as "CloudAccount_id",api_cloudaccount.organization_id,api_cloudaccount.aws_role_arn,api_cloudaccount.role_external_id,api_cloudaccount.created_time,api_cloudaccount.status_info from api_cloudaccount join api_organization on api_organization.id = api_cloudaccount.organization_id where (cloud_provider_id) = '{provider_id_search}' limit 20""")
        if df9.empty:
            print(bcolors.FAIL + "No Data Found" + bcolors.ENDC)
            exit()
        else:
            bashCommand = "whoami"
            process = subprocess.Popen(bashCommand, shell=True, executable="/bin/zsh", stdout=subprocess.PIPE)
            login_user, error = process.communicate()
            login_user_str = str(login_user).replace("\\n", "").replace("b'", "").replace("'", "")
            account_id = df9["CloudAccount_id"].to_string(index=False)
            csv_out = df9.to_csv()
            text_file = open(f"{csv_file}", "a+")
            text_file.write(csv_out)
            text_file.close()

            df_csv = pd.read_csv(f'{csv_file}', skipinitialspace=True)
            fields = ['region']
            region = df_csv.region
            location = df_csv.region.to_string(index=False)
            print(bcolors.OKCYAN + "Please open a new iTerm and run next output:"+ bcolors.ENDC +"\n")
            print(f"prp utils/api_scripts/api.py scan --api-host https://app.{location}.orcasecurity.io --jwt-tokens {jwt_token_search} --customer-account-id {account_id} --assets-to-scan {asset_id_search} --reserve-collectors {login_user_str}_collector_with_vpn --reserve-collector-backconnect-server utils/api_scripts/vpnconnect.json")
            os.remove(csv_file)
            exit()

    if args.res_s3:
        provider_id_search = getattr(args, "res_s3")[0]
        bucket_name_search = getattr(args, "res_s3")[1]
        jwt_token_search = getattr(args, "res_s3")[2]
        
        df9 = ApiDB().query_all_regions(query=f"""select api_organization.name as "Org_Name", api_cloudaccount.name as Account_Name,api_cloudaccount.id as "CloudAccount_id",api_cloudaccount.organization_id,api_cloudaccount.aws_role_arn,api_cloudaccount.role_external_id,api_cloudaccount.created_time,api_cloudaccount.status_info from api_cloudaccount join api_organization on api_organization.id = api_cloudaccount.organization_id where (cloud_provider_id) = '{provider_id_search}' limit 20""")
        if df9.empty:
            print(bcolors.FAIL + "No Data Found" + bcolors.ENDC)
            exit()
        else:
            bashCommand = "whoami"
            process = subprocess.Popen(bashCommand, shell=True, executable="/bin/zsh", stdout=subprocess.PIPE)
            login_user, error = process.communicate()
            login_user_str = str(login_user).replace("\\n", "").replace("b'", "").replace("'", "")
            account_id = df9["CloudAccount_id"].to_string(index=False)
            csv_out = df9.to_csv()
            text_file = open(f"{csv_file}", "a+")
            text_file.write(csv_out)
            text_file.close()

            df_csv = pd.read_csv(f'{csv_file}', skipinitialspace=True)
            fields = ['region']
            region = df_csv.region
            location = df_csv.region.to_string(index=False)
            print(bcolors.OKCYAN + "Please open a new iTerm and run next output:"+ bcolors.ENDC +"\n")
            print(f"prp utils/api_scripts/api.py scan --api-host https://app.{location}.orcasecurity.io --jwt-tokens {jwt_token_search} --customer-account-id {account_id} --buckets-to-scan {bucket_name_search} --reserve-s3-collectors {login_user_str}_collector_with_vpn --reserve-collector-backconnect-server utils/api_scripts/vpnconnect.json")
            os.remove(csv_file)
            exit()

    if args.res_fargate:
        provider_id_search = getattr(args, "res_fargate")[0]
        fargate_asset_id_search = getattr(args, "res_fargate")[1]
        jwt_token_search = getattr(args, "res_fargate")[2]

        df9 = ApiDB().query_all_regions(
            query=f"""select api_organization.name as "Org_Name", api_cloudaccount.name as Account_Name,api_cloudaccount.id as "CloudAccount_id",api_cloudaccount.organization_id,api_cloudaccount.aws_role_arn,api_cloudaccount.role_external_id,api_cloudaccount.created_time,api_cloudaccount.status_info from api_cloudaccount join api_organization on api_organization.id = api_cloudaccount.organization_id where (cloud_provider_id) = '{provider_id_search}' limit 20""")
        if df9.empty:
            print(bcolors.FAIL + "No Data Found" + bcolors.ENDC)
            exit()
        else:
            bashCommand = "whoami"
            process = subprocess.Popen(bashCommand, shell=True, executable="/bin/zsh", stdout=subprocess.PIPE)
            login_user, error = process.communicate()
            login_user, error = process.communicate()
            login_user_str = str(login_user).replace("\\n", "").replace("b'", "").replace("'", "")
            account_id = df9["CloudAccount_id"].to_string(index=False)
            csv_out = df9.to_csv()
            text_file = open(f"{csv_file}", "a+")
            text_file.write(csv_out)
            text_file.close()

            df_csv = pd.read_csv(f'{csv_file}', skipinitialspace=True)
            fields = ['region']
            region = df_csv.region
            location = df_csv.region.to_string(index=False)
            print(bcolors.OKCYAN + "Please open a new iTerm and run next output:" + bcolors.ENDC + "\n")
            print(
                f"prp utils/api_scripts/api.py scan --api-host https://app.{location}.orcasecurity.io --jwt-tokens {jwt_token_search} --customer-account-id {account_id} --assets-to-scan {fargate_asset_id_search} --reserve-fargate-collectors {login_user_str}_collector_with_vpn --reserve-collector-backconnect-server utils/api_scripts/vpnconnect.json")
            os.remove(csv_file)
            exit()