from flask import (
    Flask,
    render_template,
    request,
    send_file,
    flash,
    redirect,
    url_for,
    make_response,
)
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np
from io import BytesIO

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a secure secret key

ALLOWED_EXTENSIONS = {"xlsx"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part in the request.")
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            flash("No file selected.")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                xls = pd.ExcelFile(file)
                sheets_dict = {}

                for sheet in xls.sheet_names:
                    if sheet == "defaultSchools":
                        df = pd.read_excel(xls, sheet_name=sheet)
                    else:
                        df = pd.read_excel(xls, sheet_name=sheet, skiprows=3)
                        df = df.dropna(axis=1, how="all")

                    if sheet != "defaultSchools":
                        if "Total Expected Entries" not in df.columns:
                            print(
                                f"Warning: Sheet '{sheet}' does not contain the column 'Total Expected Entries'. Skipping calculations for this sheet."
                            )
                        else:
                            if sheet == "गणित":
                                df["एकूण गुण"] = df["Total Expected Entries"] * 7
                                df["प्राप्त गुण"] = (
                                    df["प्रारंभिक"] * 1
                                    + df["अंक ओळख"] * 2
                                    + df["संख्याज्ञान"] * 3
                                    + df["बेरीज"] * 4
                                    + df["वजाबाकी"] * 5
                                    + df["गुणाकार"] * 6
                                    + df["भागाकार"] * 7
                                )
                            else:
                                df["एकूण गुण"] = df["Total Expected Entries"] * 6
                                df["प्राप्त गुण"] = (
                                    df["प्रारंभिक"] * 1
                                    + df["अक्षर"] * 2
                                    + df["शब्द"] * 3
                                    + df["वाक्य"] * 4
                                    + df["परिच्छेद"] * 5
                                    + df["गोष्ट"] * 6
                                )
                            percentage = (df["प्राप्त गुण"] / df["एकूण गुण"]) * 100
                            df["टक्केवारी"] = np.floor(percentage * 100) / 100
                    sheets_dict[sheet] = df

                output = BytesIO()
                output_filename = "transformed-" + filename
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    for sheet_name, df in sheets_dict.items():
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                output.seek(0)

                # Create the file download response and set a cookie to signal success.
                response = make_response(
                    send_file(
                        output,
                        as_attachment=True,
                        download_name=output_filename,
                        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                )
                response.set_cookie("fileDownload", "true")
                return response
            except Exception as e:
                flash(f"Error processing file: {str(e)}")
                return redirect(request.url)
        else:
            flash("Invalid file type. Only Excel (.xlsx) files are allowed.")
            return redirect(request.url)
    return render_template("index.html")


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
