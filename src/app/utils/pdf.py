import base64
import os
import re
from weasyprint import HTML, CSS

def design_pdf(data):
    logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../utils/logos/Logo.png'))

    if not os.path.exists(logo_path):
        return "Logo file not found", 404

    with open(logo_path, "rb") as image_file:
        encoded_logo = base64.b64encode(image_file.read()).decode('utf-8')

    # CSS content
    css_content = """
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 50px 20px;  /* Reduce padding */
            max-width: 100%;
            box-sizing: border-box;
            background-color: #f9f9f9;
            color: #333;
            line-height: 1;
        }
        header {
            display: flex;
            flex-direction: row;  /* Align logo and client info side by side */
            justify-content: space-between;
            margin-bottom: 20px;
            align-items: flex-start;
        }
        .company-logo {
            height: 130px;  /* Reduce logo size */
            border-radius: 40%;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .client-info {
            max-width: 40%;  /* Ensure client info fits beside logo */
            font-size: 1.25em;  /* Slightly smaller font size */
            color: #777;
            text-align: left;  /* Align text to the right */
        }
        .client-info p {
            margin: 0;
            padding: 2px 0;
        }
        .title-date {
            margin-top: 0px;  /* Add margin to title-date section */
        }
        .title-date p {
            font-weight: bold;
        }
        .title-date h1 {
            font-size: 1.8em;  /* Reduce font size */
            margin: 0;
            color: #003366;
        }
        h1, h2, h3 {
            color: #003366;
            margin: 10px 0;  /* Reduce margin */
        }
        h2 {
            border-bottom: 2px solid royalblue;
            padding-bottom: 10px;
            font-size: 1.4em;  /* Reduce font size */
            font-weight: bold;
            text-transform: uppercase;
        }
        h3 {
            margin-top: 8px;
            font-size: 1.2em;  /* Reduce font size */
            color: #00529B;
            font-weight: bold;
        }
        ul {
            list-style-type: disc;
            padding-left: 20px;
            color: #555;
            font-size: 1em;  /* Adjust font size */
        }
        li {
            margin-bottom: 8px;
            line-height: 1.4;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;  /* Reduce margin */
            border: 2px solid black;  /* Reduce border thickness */
        }
        th, td {
            border: 1px solid #ddd;
            padding: 10px;  /* Adjust padding */
            text-align: left;
        }
        th {
            background-color: royalblue;
            color: white;
            font-weight: bold;
            text-align: center;
        }
        section {
            margin-bottom: 30px;  /* Reduce margin */
            background-color: #f4f4f9;
            border-left: 4px solid royalblue;  /* Reduce border width */
            padding: 15px;  /* Reduce padding */
            border-radius: 5px;
            page-break-inside: avoid;
        }
        footer {
            background-color: #333;
            color: #fff;
            text-align: center;
            padding: 10px;
            width: 100%;
            position: relative;
        }
        .footer-content {
            display: flex;
            flex-direction: column;
            align-items: center;
            line-height: 1.25;
            font-size: 0.8em;  /* Reduce font size */
        }
        .footer-content p {
            margin: 0.25em 0;
        }
                @media print {
            header, .objectives, .milestones, .risks, .qualifications {
                page-break-before: always;
            }
            .cost-breakdown-title {
                page-break-before: always;
                font-size: 20px;
                font-weight: bold;
                margin-top: 0;
                padding-top: 20px;
            }
            .first-stakeholder {
                page-break-before: avoid;
            }
            .stakeholder-section:not(:first-of-type) {
                page-break-before: always;
            }
            footer {
                display: none;
            }
            @page {
                size: auto;
                margin: 0mm;
            }
        }

    """

    # HTML content
    html_content = f"""
        <html>
        <head>
            <style>{css_content}</style>
        </head>
        <body>
            <header>
                <img src="data:image/png;base64,{encoded_logo}" alt="Company Logo" class="company-logo">
                <div class="client-info">
                    <p><strong>Company Name:</strong> {data['ClientInformation']['CompanyName']}</p>
                    <p><strong>Contact Name:</strong> {data['ClientInformation']['ContactPerson']}</p>
                    <p><strong>Address:</strong> {data['ClientInformation']['Address']}</p>
                    <p><strong>Email:</strong> {data['ClientInformation']['Email']}</p>
                    <p><strong>Phone:</strong> {data['ClientInformation']['Phone']}</p>
                </div>
            </header>
            <div class="title-date">
                <h1>{data['ProjectTitle']}</h1>
                <p>Proposal ID: {data['ProposalID']}</p>
                <p>Date: {data['Date']['CurrentDate']}</p>
            </div>
      <main>
    <section class="executive-summary">
        <h2>Executive Summary</h2>
        <p>{data['ExecutiveSummary']}</p>
    </section>
    <section class="background">
        <h2>Background</h2>
        <p>{data['Background']}</p>
    </section>
    <section class="objectives">
        <h2>Objectives</h2>
        <ul>
            {"".join(f"<li>{objective}</li>" for objective in data['Objectives'])}
        </ul>
    </section>
    

        <section class="milestones">
        <h2>Milestones</h2>
        {"".join(f"<div><h3>{milestone['MilestoneName']}</h3><ul>{''.join(f'<li>{key_deliverable}</li>' for key_deliverable in milestone['KeyDeliverables'])}</ul></div>" for milestone in data['Milestones'])}
    </section>
    <section class="risks">
        <h2>Risks</h2>
        {"".join(f"<div><h3>{risk['RiskDescription']}</h3><ul>{''.join(f'<li>{strategy}</li>' for strategy in risk['MitigationStrategies'])}</ul></div>" for risk in data['Risks'])}
    </section>

    <section class="deliverables">
        <h2>Deliverables</h2>
        <ul>
            {"".join(f"<li>{deliverable}</li>" for deliverable in data['Deliverables'])}
        </ul>
    </section>
   
    <section class="qualifications">
        <h2>Our Qualifications</h2>
        <h3>Company Profile</h3>
        <p>{data['OurQualifications']['CompanyProfile']}</p>
        <h3>Relevant Experience</h3>
        <p>{data['OurQualifications']['RelevantExperience']}</p>
        <h3>Team Expertise</h3>
        <p>{data['OurQualifications']['TeamExpertise']}</p>
    </section>
    <section class="budget">
        <h2>Budget</h2>
        <table>
            <thead>
                <tr>
                    <th>Total Estimated Hours</th>
                    <th>Total Estimated Cost</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>{format_number(data['Budget']['TotalEstimatedHours'])}</td>
                    <td>{format_currency(data['Budget']['TotalEstimatedCost'])}</td>
                </tr>
            </tbody>
        </table>
    </section>
    <section class="cost-breakdown">
        <h2 class="cost-breakdown-title">Cost Breakdown by Stakeholder</h2>
        {"".join(f'''
        <div class="stakeholder-section">
            <h4>Stakeholder: {stakeholder['Stakeholder']}</h4>
            <table>
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>Description</th>
                        <th>Hours</th>
                        <th>Total Cost</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(f'<tr><td>{detail["Item"]}</td><td>{detail["Description"]}</td><td>{format_number(detail["TotalHours"])}</td><td>{format_currency(detail["Cost"])}</td></tr>' for detail in stakeholder['Details'])}
                </tbody>
            </table>
        </div>
        ''' for stakeholder in data['Budget']['CostBreakdown'])}
    </section>
</main>

            <footer>
                <div class="footer-content">
                    <p>{data['UserInformation']['CompanyName']}</p>
                    <p>{data['UserInformation']['Website']}</p>
                    <p>{data['UserInformation']['Address']}</p>
                    <p>{data['UserInformation']['Email']}</p>
                    <p>{data['UserInformation']['Phone']}</p>
                </div>
            </footer>
        </body>
        </html>
    """

    try:
        html = HTML(string=html_content)
        css = CSS(string=css_content)
        pdf_content = html.write_pdf(stylesheets=[css])

        # # Define the folder and file names
        # proposal_data = data
        # client_company_name = sanitize_filename(proposal_data['ClientInformation']['CompanyName'])
        # project_title = sanitize_filename(proposal_data['ProjectTitle'])
        # proposal_date = proposal_data['Date']['CurrentDate']
        # sanitized_proposal_id = str(proposal_data['ProposalID']).replace('-', '')
        # folder_name = f"S{sanitized_proposal_id} - {project_title} - {client_company_name} - {proposal_date}"
        # file_name = f"S{sanitized_proposal_id} - {project_title} - Proposal - {proposal_date}.pdf"
        
        # # Define the local directory path where the file will be saved
        # local_directory = "PDFProposals"
        # local_folder_path = os.path.join(local_directory, folder_name)
        # os.makedirs(local_folder_path, exist_ok=True)

        # pdf_filename = os.path.join(local_folder_path, file_name)
        
        # # Convert HTML to PDF using pdfkit
        # with open(pdf_filename, 'wb') as pdf_file:
        #     pdf_file.write(pdf_content)

        return pdf_content
    except Exception as e:
        raise


def sanitize_filename(filename):
    """Sanitize the filename to remove any special characters."""
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

def format_currency(value):
    try:
        return "${:,.2f}".format(float(value) if value else 0)
    except ValueError:
        return "$0.00"

def format_number(value):
    try:
        return "{:,.2f}".format(float(value) if value else 0)
    except ValueError:
        return "0.00"
