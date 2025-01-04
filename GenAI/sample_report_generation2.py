# -*- coding: utf-8 -*-
"""
Created on Thu Jan  2 05:16:06 2025

@author: olanr
"""


from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from bs4 import BeautifulSoup
from typing import Dict, List
import os
import shutil


def empty_folder(folder_path):
    # Check if the folder exists
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        # Iterate through the contents of the folder
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                # Check if it is a file or directory
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # Remove file or symlink
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # Remove directory
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
    else:
        print(f"The folder '{folder_path}' does not exist or is not a directory.")
        
        
def parse_document(content):
    """Simulate parsing XML-like content."""
    styles = getSampleStyleSheet()
    elements = []
    para_count = 0
    
    soup = BeautifulSoup(content, "html.parser")
    
    if content.strip().startswith("<title>"):
        text = content.strip().replace("<title>", "").replace("</title>", "")
        elements.append(Paragraph(text, styles["Title"]))
    
    if content.strip().startswith("<paragraph>"):
        paragraph_texts = [Paragraph(para.text, styles["BodyText"]) for para in soup.find_all("paragraph")]
        
        elements.append(paragraph_texts[para_count])
        elements.append(Spacer(1, 12))
        para_count += 1
    if content.strip().startswith("<bullet>"):
        # Check if the line contains <bold> tags
        text = content.strip().replace("<bullet>", "").replace("</bullet>", "")
        if "<bold>" in text and "</bold>" in text:
            # Make bold the text inside <bold> tags
            bold_text = text.split("<bold>")[1].split("</bold>")[0]
            text = text.replace(f"<bold>{bold_text}</bold>", f"<b>{bold_text}</b>")
        bullet_style = styles["Bullet"]
        elements.append(Paragraph(f"• {text}", bullet_style))
    if content.strip().startswith("<list>"):
        elements.append(Spacer(1, 12))
    if content.strip().startswith("</list>"):
        elements.append(Spacer(1, 12))
    
    return elements


def compile_pdf_elements(topic_to_pdf_map: Dict):
    compiled_elements = []
    
    for topic in topic_to_pdf_map:
        pdf_content = topic_to_pdf_map[topic]
        pdf_elements = build_pdf_elements(pdf_content)
        compiled_elements.extend(pdf_elements)
    
    return compiled_elements


def create_pdf_report(output_file: str, compiled_pdf_elements: List, 
                      report_folder: str = "output_reports",
                      image_folder: str = "output_reports_images"):
    
    empty_folder(report_folder)

    for element in compiled_pdf_elements:
        try:
            img_filename = element.filename
        except AttributeError:
            continue
        
        img_element_exists = os.path.exists(img_filename)
        
        if not img_element_exists:
            print("DOES NOT EXISTTTTTTTTTTTT")
            element_idx = compiled_pdf_elements.index(element)
            img_header = compiled_pdf_elements[element_idx - 1]
            img_description = compiled_pdf_elements[element_idx + 1]
            
            compiled_pdf_elements.remove(element)
            compiled_pdf_elements.remove(img_header)
            compiled_pdf_elements.remove(img_description)
    
    os.makedirs(report_folder, exist_ok= True)
    output_filepath = os.path.join(report_folder, output_file)
    
    doc = SimpleDocTemplate(output_filepath, pagesize=letter)
    doc.build(compiled_pdf_elements)
    print(f"PDF successfully created at {output_filepath}")
    

    
    
    
def build_pdf_elements(pdf_content: Dict, image_folder: str = "output_reports_images"):
    pdf_elements = []
    styles = getSampleStyleSheet()
    
    sub_headers = pdf_content["sub_header"]
    texts = pdf_content["xml_text"]
    charts = pdf_content["chart_info"]
    
    for idx, sub_header in enumerate(sub_headers):
        pdf_elements.append(Paragraph(sub_header, styles["Heading2"]))
        pdf_elements.append(Spacer(1, 12))
        
        texts[idx]
        body_paragraph = parse_document(texts[idx])
        pdf_elements.extend(body_paragraph)
        pdf_elements.append(Spacer(1, 12))
        
        if len(charts[idx]) > 0:
            chart_title = charts[idx][0].chart_title
            
            os.makedirs(image_folder, exist_ok= True)
            chart_image_name = charts[idx][0].chart_image_name
            
            chart_image_path = os.path.join(image_folder, chart_image_name)
            
            print(f"YYYYYYYYYYYYYYY\n\n{chart_image_path = }")
            
            
            chart_image = Image(chart_image_path, width=300, height=300)
            
            chart_description = charts[idx][0].chart_description
            
            pdf_elements.append(Paragraph(chart_title, styles["BodyText"]))
            pdf_elements.append(chart_image)
            pdf_elements.append(Paragraph(chart_description, styles["BodyText"]))
            
            pdf_elements.append(Spacer(1, 12))
        
    return pdf_elements


