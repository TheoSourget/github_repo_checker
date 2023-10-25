import requests
import pdf_utilities.pdf_utilities as pdf_util
import re
import glob
from PyPDF2 import PdfReader 


def get_github_links():
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


def repo_isempty(repo):
    base_url = "https://api.github.com/repos/"
    repo_infos = repo.removeprefix("https://github.com/")
    repo_infos = repo_infos.split("/")
    resp = requests.get(f"{base_url}{repo_infos[0]}/{repo_infos[1]}")
    if resp.status_code == 404:
        return True
    else:
        if resp.json()["size"] == 0:
            return True
        else:
            return False

def main():
    lst_links = get_github_links()
    for link in lst_links:
        isempty = repo_isempty(link)
        print(link,isempty)
    
if __name__ == "__main__":
    main() 
