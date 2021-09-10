import argparse
import csv
import json
import sys

from core_data_modules.cleaners import Codes
from core_data_modules.cleaners.codes import SomaliaCodes
from core_data_modules.logging import Logger
from id_infrastructure.firestore_uuid_table import FirestoreUuidTable
from storage.google_cloud import google_cloud_utils

from src.lib import PipelineConfiguration

log = Logger(__name__)

TARGET_LOCATIONS = {SomaliaCodes.GALMUDUG, SomaliaCodes.SOUTH_WEST_STATE}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generates lists of phone numbers of previous IMAQAL respondents who  "
                                                 "were labelled as living in one of the target locations")

    parser.add_argument("google_cloud_credentials_file_path", metavar="google-cloud-credentials-file-path",
                        help="Path to a Google Cloud service account credentials file to use to access the "
                             "credentials bucket")
    parser.add_argument("pipeline_configuration_file_path", metavar="pipeline-configuration-file",
                        help="Path to the pipeline configuration json file")
    parser.add_argument("csv_input_file_path", metavar="csv-input-file-path", nargs="+",
                        help="Paths to csv files (either messages or individuals analysis) to extract phone "
                             "numbers from")
    parser.add_argument("csv_output_file_path", metavar="csv-output-file-path",
                        help="Path to a CSV file to write the contacts from the locations of interest to. "
                             "Exported file is in a format suitable for direct upload to Rapid Pro")

    args = parser.parse_args()

    sys.setrecursionlimit(100000)

    google_cloud_credentials_file_path = args.google_cloud_credentials_file_path
    pipeline_configuration_file_path = args.pipeline_configuration_file_path
    csv_input_file_path = args.csv_input_file_path
    csv_output_file_path = args.csv_output_file_path

    log.info("Loading Pipeline Configuration File...")
    with open(pipeline_configuration_file_path) as f:
        pipeline_configuration = PipelineConfiguration.from_configuration_file(f)
    Logger.set_project_name(pipeline_configuration.pipeline_name)
    log.debug(f"Pipeline name is {pipeline_configuration.pipeline_name}")

    log.info("Downloading Firestore UUID Table credentials...")
    firestore_uuid_table_credentials = json.loads(google_cloud_utils.download_blob_to_string(
        google_cloud_credentials_file_path,
        pipeline_configuration.uuid_table.firebase_credentials_file_url
    ))

    phone_number_uuid_table = FirestoreUuidTable.init_from_credentials(
        firestore_uuid_table_credentials,
        pipeline_configuration.uuid_table.table_name,
        "avf-phone-uuid-"
    )
    log.info("Initialised the Firestore UUID table")

    uuids = set()
    location_counts = {location: 0 for location in TARGET_LOCATIONS}
    for path in csv_input_file_path:
        # Load the data
        log.info(f"Loading previous csv data from file '{path}'...")
        with open(path, mode="r") as csv_file:
            csv_reader = csv.DictReader(csv_file)
            data = [row for row in csv_reader]
        log.info(f"Loaded {len(data)} rows")

        # Search the data for contacts from one of the relevant locations
        log.info(f"Searching for participants from the target locations ({TARGET_LOCATIONS})...")
        file_uuids = set()
        file_location_counts = {location: 0 for location in TARGET_LOCATIONS}
        for row in data:
            if row["state"] == Codes.STOP:
                continue

            location = row["state"]
            if location in TARGET_LOCATIONS:
                if "uid" not in row:
                    continue
                if row["uid"] not in file_uuids:
                    file_location_counts[location] += 1
                    file_uuids.add(row["uid"])
                if row["uid"] not in uuids:
                    location_counts[location] += 1
                    uuids.add(row["uid"])
        
        log.info(f"Found {len(file_uuids)} contacts in the target locations "
                 f"(per-location counts: {file_location_counts})")
        log.info(f"Running total: {len(uuids)} (per-location counts: {location_counts})")

    # Convert the uuids to phone numbers
    log.info(f"Converting {len(uuids)} uuids to phone numbers...")
    uuid_phone_number_lut = phone_number_uuid_table.uuid_to_data_batch(uuids)
    phone_numbers = set()
    skipped_uuids = set()
    for uuid in uuids:
        # Some uuids are no longer re-identifiable due to a uuid table consistency issue between OCHA and WorldBank-PLR
        if uuid in uuid_phone_number_lut:
            phone_numbers.add(f"+{uuid_phone_number_lut[uuid]}")
        else:
            skipped_uuids.add(uuid)
    log.info(f"Successfully converted {len(phone_numbers)} uuids to phone numbers.")
    log.warning(f"Unable to re-identify {len(skipped_uuids)} uuids")

    # Export contacts CSV
    log.warning(f"Exporting {len(phone_numbers)} phone numbers to {csv_output_file_path}...")
    with open(csv_output_file_path, "w") as f:
        writer = csv.DictWriter(f, fieldnames=["URN:Tel", "Name"], lineterminator="\n")
        writer.writeheader()

        for n in phone_numbers:
            writer.writerow({
                "URN:Tel": n
            })
        log.info(f"Wrote {len(phone_numbers)} contacts to {csv_output_file_path}")
