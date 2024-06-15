import json

from django.template.loader import render_to_string

from prelo.aws.s3_utils import html_to_pdf


def create_report_for_deck(deck):
    """
    Create a report for a pitch deck analysis
    """

    analysis = deck.analysis
    raw_report = json.loads(analysis.concerns)
    html_string = render_to_string('report_template.html',
                                   {'sections': raw_report['concerns'], 'filename': deck.s3_path.split("/")[-1],
                                    })
    print(html_string)
    # replace deck pdf file in s3 path with report.pdf
    base_path = deck.s3_path.split("/")[0:-1]
    output_path = "/".join(base_path) + "/report.pdf"
    html_to_pdf(html_string, output_path)

    return output_path
