import unittest
import os
import json
import sys
from io import StringIO
from contextlib import contextmanager
from parser import AppointmentScheduler


@contextmanager
def suppress_output():
    new_stdout = StringIO()
    new_stderr = StringIO()
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    try:
        sys.stdout = new_stdout
        sys.stderr = new_stderr
        yield
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


class TestAppointmentScheduler(unittest.TestCase):

    def setUp(self):
        self.test_file = "test_input.hl7"

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def write_hl7(self, content):
        with open(self.test_file, "w") as f:
            f.write(content)

    def test_valid_hl7_message(self):
        hl7 = (
            "MSH|^~\\&|HIS|RIH|EKG|EKG|202201011230||SIU^S12|MSG00001|P|2.4\n"
            "SCH|1234^5678|...|...|202305011230|...|...|...|Checkup|...|Room A\n"
            "PID|||123456^^^MR||Doe^John||19900101|M\n"
            "PV1||I|^^^|...|...|789^Smith^Jane"
        )
        self.write_hl7(hl7)
        with suppress_output():
            scheduler = AppointmentScheduler(self.test_file)
            result = scheduler.decode_hl7_messages()
        self.assertEqual(len(result), 1)
        appointment = result[0]
        self.assertEqual(appointment["appointment_id"], "5678")
        self.assertEqual(appointment["patient"]["first_name"], "John")
        self.assertEqual(appointment["provider"]["name"], "Dr. Jane Smith")

    def test_multiple_messages(self):
        hl7 = (
            "MSH|^~\\&|HIS|RIH|EKG|EKG|202201011230||SIU^S12|MSG00001|P|2.4\n"
            "SCH|1234^1111|...|...|202305011230|...|...|...|Consultation|...|Room B\n"
            "PID|||789101^^^MR||Smith^Anna||19880515|F\n"
            "PV1||I|^^^|...|...|555^Jones^Emily\n"
            "#\n"
            "MSH|^~\\&|HIS|RIH|EKG|EKG|202201011230||SIU^S12|MSG00002|P|2.4\n"
            "SCH|5678^2222|...|...|202306011330|...|...|...|Follow-up|...|Room C\n"
            "PID|||654321^^^MR||Brown^Bob||19791212|M\n"
            "PV1||I|^^^|...|...|666^Taylor^Chris"
        )
        self.write_hl7(hl7)
        with suppress_output():
            scheduler = AppointmentScheduler(self.test_file)
            results = scheduler.decode_hl7_messages()
        self.assertEqual(len(results), 2)

    def test_missing_segments(self):
        hl7 = (
            "MSH|^~\\&|HIS|RIH|EKG|EKG|202201011230||SIU^S12|MSG00003|P|2.4\n"
            "SCH|1234^1111|...|...|202305011230|...|...|...|Consultation|...|Room B\n"
        )
        self.write_hl7(hl7)
        with suppress_output():
            scheduler = AppointmentScheduler(self.test_file)
            results = scheduler.decode_hl7_messages()
        self.assertEqual(results, [])

    def test_invalid_date_format(self):
        hl7 = (
            "MSH|^~\\&|HIS|RIH|EKG|EKG|202201011230||SIU^S12|MSG00004|P|2.4\n"
            "SCH|1234^1111|...|...|INVALIDDATE|...|...|...|Consultation|...|Room B\n"
            "PID|||789101^^^MR||Smith^Anna||19880515|F\n"
            "PV1||I|^^^|...|...|555^Jones^Emily"
        )
        self.write_hl7(hl7)
        with suppress_output():
            scheduler = AppointmentScheduler(self.test_file)
            results = scheduler.decode_hl7_messages()
        self.assertEqual(results, [])

    def test_missing_provider(self):
        hl7 = (
            "MSH|^~\\&|HIS|RIH|EKG|EKG|202201011230||SIU^S12|MSG00005|P|2.4\n"
            "SCH|1234^1111|...|...|202305011230|...|...|...|Consultation|...|Room B\n"
            "PID|||789101^^^MR||Smith^Anna||19880515|F\n"
            "PV1||I|^^^|...|...|"
        )
        self.write_hl7(hl7)
        with suppress_output():
            scheduler = AppointmentScheduler(self.test_file)
            results = scheduler.decode_hl7_messages()
        self.assertEqual(results, [])

    def test_file_not_found(self):
        with suppress_output():
            scheduler = AppointmentScheduler("nonexistent.hl7")
            results = scheduler.decode_hl7_messages()
        self.assertEqual(results, [])


if __name__ == '__main__':
    unittest.main()
