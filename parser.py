import os
import json
from datetime import datetime


class AppointmentScheduler:

    def __init__(self, file_name):
        self.file_name = file_name
        self.file_path = self.create_input_file_path(file_name)
        self.hl7_message = self.read_hl7_file()

    def create_input_file_path(self, file_name):
        local_directory = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(local_directory, file_name)

    def read_hl7_file(self):
        try:
            with open(self.file_path, 'r') as file:
                return file.read().strip()
        except FileNotFoundError:
            print(f"File not found: {self.file_path}")
            return ""

    def decode_hl7_messages(self):
        messages = self.hl7_message.split('#')
        results = []
        for message in messages:
            if not message.strip():
                continue

            hl7_data = {
                "MSH": [''] * 19,
                "PID": [''] * 30,
                "SCH": [''] * 25,
                "PV1": [''] * 52
            }

            segments = message.strip().split('\n')
            for segment in segments:
                if segment.startswith("MSH"):
                    self.process_segment(segment, "MSH", hl7_data)
                elif segment.startswith("PID"):
                    self.process_segment(segment, "PID", hl7_data)
                elif segment.startswith("SCH"):
                    self.process_segment(segment, "SCH", hl7_data)
                elif segment.startswith("PV1"):
                    self.process_segment(segment, "PV1", hl7_data)
                else:
                    print(f"Unknown segment: {segment}")

            appointment_json = self.extract_appointment_json(hl7_data)
            if appointment_json:
                results.append(appointment_json)

        return results

    def process_segment(self, segment, segment_type, hl7_data):
        fields = segment.split('|')
        for i, field in enumerate(fields):
            if i < len(hl7_data[segment_type]):
                hl7_data[segment_type][i] = field

    def extract_appointment_json(self, hl7_data):
        sch = hl7_data["SCH"]
        pid = hl7_data["PID"]
        pv1 = hl7_data["PV1"]

        try:
            appointment_id = sch[1].split('^')[1] if len(sch) > 1 and '^' in sch[1] else sch[1]
            appointment_datetime_raw = sch[4]
            try:
                appointment_datetime = datetime.strptime(appointment_datetime_raw, '%Y%m%d%H%M').isoformat() + 'Z'
            except ValueError:
                print(f"Warning: Invalid appointment date '{appointment_datetime_raw}', skipping message.")
                return None
            
            location = sch[9] if sch[9] else "Unknown"
            reason = sch[8] if len(sch) > 8 and sch[8] else "N/A"

            patient_id = pid[3].split('^')[0] if len(pid) > 3 and pid[3] else ""
            name_parts = pid[5].split('^') if len(pid) > 5 and pid[5] else ["", ""]
            last_name = name_parts[0] if len(name_parts) > 0 else ""
            first_name = name_parts[1] if len(name_parts) > 1 else ""
            dob = datetime.strptime(pid[7], '%Y%m%d').date().isoformat() if len(pid) > 7 and pid[7] else ""
            gender = pid[8] if len(pid) > 8 else ""

            provider_raw = pv1[6] if len(pv1) > 6 and pv1[6] else ""
            provider_parts = provider_raw.split('^') if provider_raw else []
            provider_id = provider_parts[0] if len(provider_parts) > 0 else "unknown"
            provider_name = (
                f"Dr. {provider_parts[2]} {provider_parts[1]}"
                if len(provider_parts) > 2 else "Dr. Unknown"
            )

            result = {
                "appointment_id": appointment_id,
                "appointment_datetime": appointment_datetime,
                "patient": {
                    "id": patient_id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "dob": dob,
                    "gender": gender
                },
                "provider": {
                    "id": provider_id,
                    "name": provider_name
                },
                "location": location,
                "reason": reason
            }

            if self.validate_result(result):
                return result
            else:
                return None

        except Exception as e:
            print("Error decoding HL7 message:", e)
            return None

    def validate_result(self, data):
        if not data["appointment_id"] or not data["appointment_datetime"]:
            print("Warning: Missing appointment fields")
            return False
        for field in ["id", "first_name", "last_name", "dob", "gender"]:
            if not data["patient"].get(field):
                print(f"Warning: Missing field patient.{field}")
                return False
        if data["provider"]["id"] == "unknown":
            print("Warning: Missing field provider.id")
            return False
        return True

    def to_json(self):
        results = self.decode_hl7_messages()
        return json.dumps(results, indent=2)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python3 filename.py <input.hl7>")
        sys.exit(1)

    input_file = sys.argv[1]
    scheduler = AppointmentScheduler(input_file)
    print(scheduler.to_json())
