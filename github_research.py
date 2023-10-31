import requests
import pdf_utilities.pdf_utilities as pdf_util
import re
import glob
from PyPDF2 import PdfReader 
import pandas as pd
from tqdm import tqdm

def get_github_links_from_pdf():
    lst_github_repo = []
    regex = "(https:\\/\\/github\\.com\\/[^\\s\\\\]*)" #Regex for github link
    
    for pdf_path in glob.glob("./pdfs/*.pdf"):
        reader = PdfReader(pdf_path)

        #Search in abstract
        text = pdf_util.extract_section(pdf_path,"abstract")
        text = " ".join(text)
        if text:
            matched_str =  re.findall(regex,text)
            if matched_str:
                for m in matched_str:
                    lst_github_repo.append(m)
         
        text = pdf_util.extract_section(pdf_path,"Introduction")
        text = " ".join(text)
        if text:
            matched_str =  re.findall(regex,text)
            if matched_str:
                for m in matched_str:
                    lst_github_repo.append(m)
    return lst_github_repo

def get_github_links_from_csv():
    csv = pd.read_csv("./github_links.csv")
    return csv["link"].to_list()

def repo_isempty(repo):
    try:
        headers = {'Authorization': 'token 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'}
        base_url = "https://api.github.com/repos/"
        repo_infos = repo.removeprefix("https://github.com/")
        repo_infos = repo_infos.removesuffix(".git")
        repo_infos = repo_infos.split("/")
        resp = requests.get(f"{base_url}{repo_infos[0]}/{repo_infos[1]}",headers=headers)
        is_empty = None
        if resp.status_code == 404:
            is_empty = (True,404)
        elif resp.status_code == 403:
            print(resp.headers)
            return (None,403)
        else:
            if resp.json()["size"] == 0:
                is_empty = (True,200)
            elif resp.json()["size"] > 10:
                is_empty = (False,200)
            else:
                resp = requests.get(f"{base_url}{repo_infos[0]}/{repo_infos[1]}/commits",headers=headers)
                if len(resp.json()) < 3:
                    is_empty = (True,200)
                else:
                    is_empty = (False,200)
        return is_empty
    except:
        return (True,400)
def main():
    # lst_links_pdf = get_github_links_from_pdf()
    # for link in lst_links_pdf:
    #     isempty = repo_isempty(link)
    #     print(link,isempty) 

    lst_links_csv = get_github_links_from_csv()
    lst_empty = []
    lst_status_code = []
    
    
    with open("./repo_isempty_results.csv","w") as results_file:
        results_file.write("link,isempty,status_code")
        for link in tqdm(lst_links_csv):
            isempty,status_code = repo_isempty(link)
            if status_code == 403:
                print("API rate limit reached, wait an hour")
                break
            lst_empty.append(isempty)
            lst_status_code.append(status_code)
            results_file.write(f"\n{link},{isempty},{status_code}")
            
        # for i in range(len(lst_empty)):
        #     link = lst_links_csv[i]
        #     isempty = lst_empty[i]
        #     status_code = lst_status_code[i]


if __name__ == "__main__":
    main() 
