import unittest
from urllib.parse import quote
from unittest import TestCase
from datetime import datetime
from unittest.mock import patch, ANY

from quickbooks.objects import Bill, Invoice, Payment, BillPayment

from tests.integration.test_base import QuickbooksUnitTestCase
from tests.unit.test_client import MockSession

from quickbooks.objects.base import PhoneNumber, QuickbooksBaseObject
from quickbooks.objects.department import Department
from quickbooks.objects.customer import Customer
from quickbooks.objects.journalentry import JournalEntry, JournalEntryLine
from quickbooks.objects.recurringtransaction import RecurringTransaction
from quickbooks.objects.salesreceipt import SalesReceipt
from quickbooks.mixins import ObjectListMixin


class ToJsonMixinTest(unittest.TestCase):
    def test_to_json(self):
        phone = PhoneNumber()
        phone.FreeFormNumber = "555-555-5555"

        json = phone.to_json()

        self.assertEqual(json, '{\n    "FreeFormNumber": "555-555-5555"\n}')


class FromJsonMixinTest(unittest.TestCase):
    def setUp(self):
        self.json_data = {
            'DocNumber': '123',
            'TotalAmt': 100,
            'Line': [
                {
                    "Id": "0",
                    "Description": "Test",
                    "Amount": 25.54,
                    "DetailType": "JournalEntryLineDetail",
                    "JournalEntryLineDetail": {
                        "PostingType": "Debit",
                    }
                },
            ],
        }

    def test_from_json(self):
        entry = JournalEntry()
        new_obj = entry.from_json(self.json_data)

        self.assertEqual(type(new_obj), JournalEntry)
        self.assertEqual(new_obj.DocNumber, "123")
        self.assertEqual(new_obj.TotalAmt, 100)

        line = new_obj.Line[0]
        self.assertEqual(type(line), JournalEntryLine)
        self.assertEqual(line.Description, "Test")
        self.assertEqual(line.Amount, 25.54)
        self.assertEqual(line.DetailType, "JournalEntryLineDetail")
        self.assertEqual(line.JournalEntryLineDetail.PostingType, "Debit")

    def test_from_json_missing_detail_object(self):
        test_obj = QuickbooksBaseObject()

        new_obj = test_obj.from_json(self.json_data)

        self.assertEqual(type(new_obj), QuickbooksBaseObject)
        self.assertEqual(new_obj.DocNumber, "123")
        self.assertEqual(new_obj.TotalAmt, 100)


class ToDictMixinTest(unittest.TestCase):
    def test_to_dict(self):
        json_data = {
            'DocNumber': '123',
            'TotalAmt': 100,
            'Line': [
                {
                    "Id": "0",
                    "Description": "Test",
                    "Amount": 25.54,
                    "DetailType": "JournalEntryLineDetail",
                    "JournalEntryLineDetail": {
                        "PostingType": "Debit",
                    }
                },
            ],
        }

        entry = JournalEntry.from_json(json_data)
        expected = {
            'DocNumber': '123',
            'SyncToken': 0,
            'domain': 'QBO',
            'TxnDate': '',
            'TotalAmt': 100,
            'ExchangeRate': 1,
            'CurrencyRef': None,
            'PrivateNote': '',
            'sparse': False,
            'Line': [{
                'LinkedTxn': [],
                'Description': 'Test',
                'JournalEntryLineDetail': {
                    'TaxAmount': 0,
                    'Entity': None,
                    'DepartmentRef': None,
                    'TaxCodeRef': None,
                    'BillableStatus': None,
                    'TaxApplicableOn': 'Sales',
                    'PostingType': 'Debit',
                    'AccountRef': None,
                    'ClassRef': None,
                },
                'DetailType': 'JournalEntryLineDetail',
                'LineNum': 0,
                'Amount': 25.54,
                'CustomField': [],
                'Id': '0',
            }],
            'Adjustment': False,
            'Id': None,
            'TxnTaxDetail': None,
        }

        self.assertEqual(expected, entry.to_dict())


class ListMixinTest(QuickbooksUnitTestCase):
    @patch('quickbooks.mixins.ListMixin.query')
    def test_all(self, query):
        query.return_value = []
        Department.all()
        query.assert_called_once_with("SELECT * FROM Department MAXRESULTS 100", qb=ANY)

    def test_all_with_qb(self):
        self.qb_client.session = MockSession()  # Add a mock session
        with patch.object(self.qb_client, 'query') as query:
            Department.all(qb=self.qb_client)
            query.assert_called_once()

    @patch('quickbooks.mixins.ListMixin.where')
    def test_filter(self, where):
        Department.filter(max_results=25, start_position='1', Active=True)
        where.assert_called_once_with("Active = True", max_results=25, start_position='1',
                                      order_by='', qb=None)

    def test_filter_with_qb(self):
        with patch.object(self.qb_client, 'query') as query:
            Department.filter(Active=True, qb=self.qb_client)
            self.assertTrue(query.called)

    @patch('quickbooks.mixins.ListMixin.query')
    def test_where(self, query):
        Department.where("Active=True", start_position=1, max_results=10)
        query.assert_called_once_with("SELECT * FROM Department WHERE Active=True STARTPOSITION 1 MAXRESULTS 10",
                                      qb=None)

    @patch('quickbooks.mixins.ListMixin.query')
    def test_where_start_position_0(self, query):
        Department.where("Active=True", start_position=0, max_results=10)
        query.assert_called_once_with("SELECT * FROM Department WHERE Active=True STARTPOSITION 0 MAXRESULTS 10",
                                      qb=None)

    def test_where_with_qb(self):
        with patch.object(self.qb_client, 'query') as query:
            Department.where("Active=True", start_position=1, max_results=10, qb=self.qb_client)
            self.assertTrue(query.called)

    @patch('quickbooks.mixins.QuickBooks.query')
    def test_query(self, query):
        select = "SELECT * FROM Department WHERE Active=True"
        Department.query(select)
        query.assert_called_once_with(select)

    def test_query_with_qb(self):
        with patch.object(self.qb_client, 'query') as query:
            select = "SELECT * FROM Department WHERE Active=True"
            Department.query(select, qb=self.qb_client)
            self.assertTrue(query.called)

    @patch('quickbooks.mixins.ListMixin.where')
    def test_choose(self, where):
        Department.choose(['name1', 'name2'], field="Name")
        where.assert_called_once_with("Name in ('name1', 'name2')", qb=None)

    def test_choose_with_qb(self):
        with patch.object(self.qb_client, 'query') as query:
            Department.choose(['name1', 'name2'], field="Name", qb=self.qb_client)
            self.assertTrue(query.called)

    @patch('quickbooks.mixins.QuickBooks.query')
    def test_count(self, query):
        count = Department.count(where_clause="Active=True", qb=self.qb_client)
        query.assert_called_once_with("SELECT COUNT(*) FROM Department WHERE Active=True")

    @patch('quickbooks.mixins.ListMixin.query')
    def test_order_by(self, query):
        Customer.filter(Active=True, order_by='DisplayName')
        query.assert_called_once_with("SELECT * FROM Customer WHERE Active = True ORDERBY DisplayName", qb=None)

    def test_order_by_with_qb(self):
        with patch.object(self.qb_client, 'query') as query:
            Customer.filter(Active=True, order_by='DisplayName', qb=self.qb_client)
            self.assertTrue(query.called)


class ReadMixinTest(QuickbooksUnitTestCase):
    @patch('quickbooks.mixins.QuickBooks.get_single_object')
    def test_get(self, get_single_object):
        Department.get(1)
        get_single_object.assert_called_once_with("Department", pk=1, params=None)

    def test_get_with_qb(self):
        with patch.object(self.qb_client, 'get_single_object') as get_single_object:
            Department.get(1, qb=self.qb_client)
            self.assertTrue(get_single_object.called)


class UpdateMixinTest(QuickbooksUnitTestCase):
    @patch('quickbooks.mixins.QuickBooks.create_object')
    def test_save_create(self, create_object):
        department = Department()
        department.save(qb=self.qb_client)
        create_object.assert_called_once_with("Department", department.to_json(), request_id=None, params=None)

    def test_save_create_with_qb(self):
        with patch.object(self.qb_client, 'create_object') as create_object:
            department = Department()
            department.save(qb=self.qb_client)
            self.assertTrue(create_object.called)

    @patch('quickbooks.mixins.QuickBooks.update_object')
    def test_save_update(self, update_object):
        department = Department()
        department.Id = 1
        json = department.to_json()

        department.save(qb=self.qb_client)
        update_object.assert_called_once_with("Department", json, request_id=None, params=None)

    def test_save_update_with_qb(self):
        with patch.object(self.qb_client, 'update_object') as update_object:
            department = Department()
            department.Id = 1
            json = department.to_json()

            department.save(qb=self.qb_client)
            self.assertTrue(update_object.called)


class DownloadPdfTest(QuickbooksUnitTestCase):
    @patch('quickbooks.client.QuickBooks.download_pdf')
    def test_download_invoice(self, download_pdf):
        receipt = SalesReceipt()
        receipt.Id = "1"

        receipt.download_pdf(self.qb_client)
        download_pdf.assert_called_once_with('SalesReceipt', "1")

    def test_download_missing_id(self):
        from quickbooks.exceptions import QuickbooksException

        receipt = SalesReceipt()
        self.assertRaises(QuickbooksException, receipt.download_pdf)


class ObjectListTest(unittest.TestCase):

    def setUp(self):
        class TestSubclass(ObjectListMixin):

            def __init__(self, obj_list):
                super(TestSubclass, self).__init__()
                self._object_list = obj_list

        self.TestSubclass = TestSubclass

    def test_object_list_mixin_with_primitives(self):

        test_primitive_list = [1, 2, 3]
        test_subclass_primitive_obj = self.TestSubclass(test_primitive_list)
        self.assertEqual(test_primitive_list, test_subclass_primitive_obj[:])

        for index in range(0, len(test_subclass_primitive_obj)):
            self.assertEqual(test_primitive_list[index], test_subclass_primitive_obj[index])

        for prim in test_subclass_primitive_obj:
            self.assertEqual(True, prim in test_subclass_primitive_obj)

        self.assertEqual(3, test_subclass_primitive_obj.pop())
        test_subclass_primitive_obj.append(4)
        self.assertEqual([1, 2, 4], test_subclass_primitive_obj[:])

        test_subclass_primitive_obj[0] = 5
        self.assertEqual([5, 2, 4], test_subclass_primitive_obj[:])

        del test_subclass_primitive_obj[0]
        self.assertEqual([2, 4], test_subclass_primitive_obj[:])

        self.assertEqual([4, 2], list(reversed(test_subclass_primitive_obj)))

    def test_object_list_mixin_with_qb_objects(self):

        pn1, pn2, pn3, pn4, pn5 = PhoneNumber(), PhoneNumber(), PhoneNumber(), PhoneNumber(), PhoneNumber()
        test_object_list = [pn1, pn2, pn3]
        test_subclass_object_obj = self.TestSubclass(test_object_list)
        self.assertEqual(test_object_list, test_subclass_object_obj[:])

        for index in range (0, len(test_subclass_object_obj)):
            self.assertEqual(test_object_list[index], test_subclass_object_obj[index])

        for obj in test_subclass_object_obj:
            self.assertEqual(True, obj in test_subclass_object_obj)

        self.assertEqual(pn3, test_subclass_object_obj.pop())
        test_subclass_object_obj.append(pn4)
        self.assertEqual([pn1, pn2, pn4], test_subclass_object_obj[:])

        test_subclass_object_obj[0] = pn5
        self.assertEqual([pn5, pn2, pn4], test_subclass_object_obj[:])

        del test_subclass_object_obj[0]
        self.assertEqual([pn2, pn4], test_subclass_object_obj[:])

        self.assertEqual([pn4, pn2], list(reversed(test_subclass_object_obj)))


class DeleteMixinTest(QuickbooksUnitTestCase):
    def test_delete_unsaved_exception(self):
        from quickbooks.exceptions import QuickbooksException

        bill = Bill()
        self.assertRaises(QuickbooksException, bill.delete, qb=self.qb_client)

    @patch('quickbooks.mixins.QuickBooks.delete_object')
    def test_delete(self, delete_object):
        bill = Bill()
        bill.Id = 1
        bill.delete(qb=self.qb_client)

        self.assertTrue(delete_object.called)


class DeleteNoIdMixinTest(QuickbooksUnitTestCase):
    @patch('quickbooks.mixins.QuickBooks.delete_object')
    def test_delete(self, delete_object):
        recurring_txn = RecurringTransaction()
        recurring_txn.Bill = Bill()
        recurring_txn.delete(qb=self.qb_client)

        self.assertTrue(delete_object.called)


class SendMixinTest(QuickbooksUnitTestCase):
    @patch('quickbooks.mixins.QuickBooks.misc_operation')
    def test_send(self, mock_misc_op):
        invoice = Invoice()
        invoice.Id = 2
        invoice.send(qb=self.qb_client)

        mock_misc_op.assert_called_with("invoice/2/send", None, 'application/octet-stream')

    @patch('quickbooks.mixins.QuickBooks.misc_operation')
    def test_send_with_send_to_email(self, mock_misc_op):
        invoice = Invoice()
        invoice.Id = 2
        email = "test@email.com"
        send_to_email = quote(email, safe='')

        invoice.send(qb=self.qb_client, send_to=email)

        mock_misc_op.assert_called_with("invoice/2/send?sendTo={}".format(send_to_email), None, 'application/octet-stream')


class VoidMixinTest(QuickbooksUnitTestCase):
    @patch('quickbooks.mixins.QuickBooks.post')
    def test_void_invoice(self, post):
        invoice = Invoice()
        invoice.Id = 2
        invoice.void(qb=self.qb_client)
        self.assertTrue(post.called)

    @patch('quickbooks.mixins.QuickBooks.post')
    def test_void_payment(self, post):
        payment = Payment()
        payment.Id = 2
        payment.void(qb=self.qb_client)
        self.assertTrue(post.called)

    @patch('quickbooks.mixins.QuickBooks.post')
    def test_void_sales_receipt(self, post):
        sales_receipt = SalesReceipt()
        sales_receipt.Id = 2
        sales_receipt.void(qb=self.qb_client)
        self.assertTrue(post.called)

    @patch('quickbooks.mixins.QuickBooks.post')
    def test_void_bill_payment(self, post):
        bill_payment = BillPayment()
        bill_payment.Id = 2
        bill_payment.void(qb=self.qb_client)
        self.assertTrue(post.called)

    def test_delete_unsaved_exception(self):
        from quickbooks.exceptions import QuickbooksException

        invoice = Invoice()
        self.assertRaises(QuickbooksException, invoice.void, qb=self.qb_client)
