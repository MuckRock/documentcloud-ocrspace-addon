"""
This is an example OCR add-on.  It demonstrates how to write a custom OCR
add-on for DocumentCloud, using the editable text APIs
"""

import os
import json
import requests
from documentcloud.addon import AddOn
from listcrunch import uncrunch

URL = "https://api.ocr.space/parse/image"


class OCRSpace(AddOn):
    """OCR your documents using OCRSpace"""

    def main(self):
        for document in self.get_documents():
            # get the dimensions of the pages
            page_spec = [map(float, p.split("x")) for p in uncrunch(document.page_spec)]
            if document.access != "public":
                self.set_message("Document must be public")
                return
            data = {
                "url": document.pdf_url,
                "isOverlayRequired": True,
                "language": document.language,
            }
            resp = requests.post(URL, headers={"apikey": os.environ["KEY"]}, data=data)
            results = json.loads(resp.text)
            if results["IsErroredOnProcessing"]:
                self.set_message(f"Error")
                return
            pages = []
            for i, (page_results, (width, height)) in enumerate(
                zip(results["ParsedResults"], page_spec)
            ):
                # ocrspace dimensions need a correction factor for some reason
                width *= (4/3)
                height *= (4/3)

                page = {
                    "page_number": i,
                    "text": page_results["ParsedText"],
                    "ocr": "ocrspace1",
                    "positions": [],
                }
                for line in page_results["TextOverlay"]["Lines"]:
                    for word in line["Words"]:
                        page["positions"].append(
                            {
                                "text": word["WordText"],
                                "x1": (word["Left"] ) / width,
                                "y1": (word["Top"] ) / height,
                                "x2": (word["Left"] + word["Width"] ) / width,
                                "y2": (word["Top"] + word["Height"] ) / height,
                            }
                        )
                pages.append(page)
            self.client.patch(f"documents/{document.id}/", {"pages": pages})

if __name__ == "__main__":
    OCRSpace().main()
