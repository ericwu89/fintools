import argparse
import json
import logging
import time

from datetime import datetime

log = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("-filename", "--filename",
                    help="Filename of JSON transactions record")
args = parser.parse_args()


# TODO: consider leap years
YEAR_SECONDS = 60 * 60 * 24 * 365

class CapGainsCalculator(object):

    def __init__(self, filename):
        with open(filename, 'r') as f:
            self.txns = json.load(f)

    def _GetPerTxnGain(self, txn):
        """
        Returns:
            {
                "long_term": long term gain,
                "short_term": short term gain"
            }
        """
        gains = {
            "short_term": 0,
            "long_term": 0
        }
        txn_date_sec = self._TimestampSec(txn["Date"])
        log.info('Transaction date: %s', txn["Date"])
        for detail in txn["TransactionDetails"]:
            detail = detail["Details"]
            vest_date_sec = self._TimestampSec(detail["VestDate"])
            txn_gain = self._TxnDetailGain(detail)

            if not detail["Type"] == "RS":
                continue
            if txn_date_sec > YEAR_SECONDS + vest_date_sec:
                gains["long_term"] += txn_gain
                log.info('\t[Vest %s] long term gain:\t%f',
                         detail["VestDate"], txn_gain)
            else:
                gains["short_term"] += txn_gain
                log.info('\t[Vest %s] short term gain:\t%f',
                         detail["VestDate"], txn_gain)
        return gains

    def _TimestampSec(self, date_str):
        return time.mktime(datetime.strptime(date_str, "%m/%d/%Y").timetuple())

    def _TxnDetailGain(self, txn_detail):
        shares = float(txn_detail["Shares"]) 
        sale_price = float(txn_detail["SalePrice"].lstrip('$'))
        vest_price = float(txn_detail["VestFairMarketValue"].lstrip('$'))
        log.info('\t[%f shares] Vest: %f, Sale: %f',
                 shares, vest_price, sale_price)
        return shares * (sale_price - vest_price)

    def Calculate(self):
        # Keep track of short term and long term gains and losses
        long_term = 0.0
        short_term = 0.0
        log.info('Total of %d transactions', len(self.txns["Transactions"]))
        for txn in self.txns["Transactions"]:
            gains = self._GetPerTxnGain(txn)
            long_term += gains["long_term"]
            short_term += gains["short_term"]

        log.info("Results:")
        log.info("Long term:\t%d", long_term)
        log.info("Short term:\t%d", short_term)
        return long_term, short_term


if __name__ == "__main__": 
    logging.basicConfig(
            filename='cap_gains_calculator.log.INFO', level=logging.INFO)
    calculator = CapGainsCalculator(args.filename)
    long_term, short_term = calculator.Calculate()

    print("Long term:\t%d" % long_term)
    print("Short term:\t%d" % short_term)

