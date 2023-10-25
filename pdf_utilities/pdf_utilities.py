#Libraries to extract and save images
import fitz
import io
from PIL import Image

#Libraries to extract tables
import camelot
import ghostscript

#Library to extract section
from PyPDF2 import PdfReader 
import re

def extract_images(pdf_path,save_folder=None):
    """
    Extract all images within the given pdf, code inspired by https://www.geeksforgeeks.org/how-to-extract-images-from-pdf-in-python/
    Raise an exception if the path is not a valid pdf file
    Exemple of usage: extract_images(pdf_path="./pdf/exemple.pdf",save_folder="./save/")
    @params:    
        - pdf_path (String): Path of the pdf file from which images will be extracted
        - save_folder (String): None if no saving or path to saving directory in which images will be saved
    @return:
        - list of PIL images extracted from the pdf 
    """
    #Try to open the pdf
    pdf_file = fitz.open(pdf_path)
    
    #list of extracted images that will be returned
    all_images = []

    #Number of images, the name of the stored image will be its associated number 
    nb_images = 0
    for page_index in range(len(pdf_file)):
        page = pdf_file[page_index]
        images_list = page.get_images()
        for image_index, img in enumerate(images_list, start=1):
            xref = img[0]
            # extract the image bytes
            base_image = pdf_file.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            #Create Image object 
            img = Image.open(io.BytesIO(image_bytes))
            all_images.append(img)
            
            #Save into save_folder directory if it's not None
            if save_folder:
                img.save(f"{save_folder.removesuffix('/')}/{nb_images}.{image_ext}")
            
            nb_images += 1

    return all_images


def extract_tables(pdf_path):
    """
    Extract tables from a pdf file using camelot library and a post-processing step to reduce the number of false detection. 
    The post-processing step removes elements that do not contain "Table"
    Exemple of usage: extract_tables(pdf_path="./pdf/exemple.pdf")
    @params:
        -pdf_path (String): Path of the pdf file from which images will be extracted
    @return:
        - list of table
    """
    tables = camelot.read_pdf(pdf_path, "all",flavor="stream",row_tol=50)
    filtered_detection = []
    for t in tables:
        str_table = t.df.to_string()
        if re.search(f"Table", str_table,re.IGNORECASE):
            filtered_detection.append(t)
            print(t.df.to_string())
    return filtered_detection


def extract_section(pdf_path,section_query,format="numerical"):
    """
    Extract the content of a section in a pdf if the section is found.
    First, the sections' name are detected using the regular expression from the format parameter.
    Then, search for a section's name which contains the section_query parameter.
    Finally, if one is found, the content between this section's name and the next one will be returned.
    Exemple of usage: extract_section(pdf_path="./pdf/test.pdf",section_query="Results",format="roman")
    @Params:
        -pdf_path (String): path of the pdf use for the extraction
        -section_query (String): name of the section you want to extract
        -format (String): format of sections' name: "numerical" (ex: 4 Results), "roman" (ex: IV: Results), custom regex string
    @Return:
        If the section is found: an array in which each element is a line of the section
        Else: None
    """
    
    #Load the pdf
    reader = PdfReader(pdf_path)
    all_text = []
    #Go throught all the page
    for page in reader.pages:
        #Extract the text and transform it into an array
        text = page.extract_text(0).split("\n")

        #Go through the element to merge a line that finish with an - (word not ended) with the next line to only have complete words.
        idx = 1
        while idx < len(text):
            line = text[idx].strip()

            #Empty line
            if not line:
                idx += 1
                continue
           
            #Merge the lines
            while line[-1] == '-' and idx < len(text):
                line = line.removesuffix("-")
                if idx +1 < len(text):
                    line += text[idx+1]
                    idx +=1
             
            all_text.append(line)
            idx += 1
    
    if format=="roman":
        #Search for lines with the format like "IV. Introduction" which should be section's name
        regex = '(^([IVX]+\\.?) (.+)$)'
    elif format == "numerical":
        #Search for lines with the format like "1 Introduction" which should be section's name
        regex = '(^([0-9]{1,2}+\\.?) ([^ ]+(\\s)?){1,6}$)'
    else:
        regex = format
    
    #Get the indexes of line which respect the regex for section name   
    section_idx_unprocessed = [i for i, item in enumerate(all_text) if re.search(f"{regex}|(^abstract)|(^acknowledgment(s)?$)|(^reference(s)?$)|(^appendices$)", item,re.IGNORECASE)]
    if section_idx_unprocessed:
        #Remove list detection
        section_idx = []
        for i in range(len(section_idx_unprocessed)-1):
           if not section_idx_unprocessed[i] == section_idx_unprocessed[i+1] - 1:
               section_idx.append(section_idx_unprocessed[i])
        section_idx.append(section_idx_unprocessed[-1])

        #Search for the query inside detected sections' name
        sections_name = [all_text[s_idx] for s_idx in section_idx]
        
        for idx,name in enumerate(sections_name):
            #If found, return the lines between the section title (included) and the next section title (not included)
            if section_query.lower() in name.lower():
                if idx+1 < len(section_idx):
                    return all_text[section_idx[idx]:section_idx[idx+1]]
                else:
                    return all_text[section_idx[idx]:]
            
    #If no match is found, return None
    return None