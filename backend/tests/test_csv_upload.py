import unittest

from fastapi.testclient import TestClient

from app.main import app


class CsvUploadIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_upload_store_score_and_list_transactions(self):
        csv_content = (
            "transaction_id,customer_id,amount,merchant_category,country,hour_of_day,is_weekend,device_type,transaction_velocity\n"
            ",,5395.00,travel,FR,2,true,mobile,9\n"
        )
        response = self.client.post(
            "/api/transactions/upload",
            files={"file": ("transactions.csv", csv_content, "text/csv")},
        )
        self.assertEqual(response.status_code, 200, response.text)
        uploaded = response.json()["transactions"][0]
        self.assertTrue(uploaded["transaction_id"].startswith("txn_"))
        self.assertTrue(uploaded["customer_id"].startswith("cust_upload_"))
        self.assertEqual(uploaded["transaction_summary"], "Travel transaction in FR for $5,395.00")

        prediction = self.client.post("/api/predict", json={"transaction_id": uploaded["transaction_id"]})
        self.assertEqual(prediction.status_code, 200, prediction.text)
        listed = self.client.get("/api/transactions")
        self.assertTrue(any(item["transaction_id"] == uploaded["transaction_id"] for item in listed.json()))

    def test_invalid_csv_returns_row_validation_errors(self):
        csv_content = "amount,merchant_category,country,hour_of_day,is_weekend,device_type,transaction_velocity\n-1,fuel,ZZ,24,maybe,mobile,1\n"
        response = self.client.post(
            "/api/transactions/upload",
            files={"file": ("invalid.csv", csv_content, "text/csv")},
        )
        self.assertEqual(response.status_code, 422)
        self.assertTrue(response.json()["detail"]["issues"])


if __name__ == "__main__":
    unittest.main()
