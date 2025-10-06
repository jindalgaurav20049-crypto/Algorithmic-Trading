"""
Zerodha Transaction Charges Calculator
Implements exact charges for both CNC (Delivery) and MIS (Intraday) as of 2025
"""

class ZerodhaCharges:
    """Calculate transaction charges for Zerodha trades"""
    
    @staticmethod
    def calculate_cnc_charges(buy_value, sell_value):
        """
        Calculate CNC (Delivery) charges
        
        Args:
            buy_value: Total buy transaction value in INR
            sell_value: Total sell transaction value in INR
            
        Returns:
            dict: Breakdown of all charges
        """
        charges = {}
        
        # Brokerage
        charges['brokerage'] = 0.0  # ₹0 for CNC
        
        # STT (0.1% on both buy and sell)
        charges['stt_buy'] = buy_value * 0.001
        charges['stt_sell'] = sell_value * 0.001
        charges['stt_total'] = charges['stt_buy'] + charges['stt_sell']
        
        # Transaction charges (0.00297% on both buy and sell)
        charges['txn_buy'] = buy_value * 0.0000297
        charges['txn_sell'] = sell_value * 0.0000297
        charges['txn_total'] = charges['txn_buy'] + charges['txn_sell']
        
        # SEBI fees (₹10 per crore on both buy and sell)
        charges['sebi_buy'] = (buy_value / 10000000) * 10
        charges['sebi_sell'] = (sell_value / 10000000) * 10
        charges['sebi_total'] = charges['sebi_buy'] + charges['sebi_sell']
        
        # GST (18% on transaction + SEBI)
        gst_base = charges['txn_total'] + charges['sebi_total']
        charges['gst'] = gst_base * 0.18
        
        # Stamp duty (0.015% on buy, max ₹1,500 per crore)
        stamp_duty = buy_value * 0.00015
        max_stamp = (buy_value / 10000000) * 1500
        charges['stamp_duty'] = min(stamp_duty, max_stamp)
        
        # DP charges (₹15.34 per scrip on sell)
        charges['dp_charges'] = 15.34
        
        # Total charges
        charges['total'] = (charges['stt_total'] + charges['txn_total'] + 
                           charges['sebi_total'] + charges['gst'] + 
                           charges['stamp_duty'] + charges['dp_charges'])
        
        return charges
    
    @staticmethod
    def calculate_mis_charges(buy_value, sell_value):
        """
        Calculate MIS (Intraday) charges
        
        Args:
            buy_value: Total buy transaction value in INR
            sell_value: Total sell transaction value in INR
            
        Returns:
            dict: Breakdown of all charges
        """
        charges = {}
        
        # Brokerage (Flat ₹20 or 0.03% per order, whichever is lower)
        brokerage_buy = min(20, buy_value * 0.0003)
        brokerage_sell = min(20, sell_value * 0.0003)
        charges['brokerage_buy'] = brokerage_buy
        charges['brokerage_sell'] = brokerage_sell
        charges['brokerage'] = brokerage_buy + brokerage_sell
        
        # STT (0.025% on sell only)
        charges['stt'] = sell_value * 0.00025
        
        # Transaction charges (0.00297% on both buy and sell)
        charges['txn_buy'] = buy_value * 0.0000297
        charges['txn_sell'] = sell_value * 0.0000297
        charges['txn_total'] = charges['txn_buy'] + charges['txn_sell']
        
        # SEBI fees (₹10 per crore on both buy and sell)
        charges['sebi_buy'] = (buy_value / 10000000) * 10
        charges['sebi_sell'] = (sell_value / 10000000) * 10
        charges['sebi_total'] = charges['sebi_buy'] + charges['sebi_sell']
        
        # GST (18% on brokerage + transaction + SEBI)
        gst_base = charges['brokerage'] + charges['txn_total'] + charges['sebi_total']
        charges['gst'] = gst_base * 0.18
        
        # Stamp duty (0.003% on buy)
        charges['stamp_duty'] = buy_value * 0.00003
        
        # No DP charges for MIS
        charges['dp_charges'] = 0.0
        
        # Total charges
        charges['total'] = (charges['brokerage'] + charges['stt'] + 
                           charges['txn_total'] + charges['sebi_total'] + 
                           charges['gst'] + charges['stamp_duty'])
        
        return charges
    
    @staticmethod
    def get_commission_percentage(trade_value, mode='MIS'):
        """
        Get commission as percentage of trade value
        
        Args:
            trade_value: Value of the trade in INR
            mode: 'CNC' or 'MIS'
            
        Returns:
            float: Commission as percentage (e.g., 0.001 for 0.1%)
        """
        if mode.upper() == 'CNC':
            charges = ZerodhaCharges.calculate_cnc_charges(trade_value, trade_value)
        else:
            charges = ZerodhaCharges.calculate_mis_charges(trade_value, trade_value)
        
        return charges['total'] / (2 * trade_value)
