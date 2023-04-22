import xlsxwriter

def generate_excel_file(workbook_name:str, worksheet_name:str, headers_list:list, data:list):
    workbook = xlsxwriter.Workbook(workbook_name)
    worksheet = workbook.add_worksheet(worksheet_name)

    for index, header in enumerate(headers_list):
        worksheet.write(0, index, str(header).title())

    for index, entry in enumerate(data):
        for index1, header in enumerate(headers_list):
            worksheet.write(index+1, index1, entry[header])

    workbook.close()