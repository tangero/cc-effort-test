<?php
class BillingCalculator {
  public function invoice($account, $usageCents, $periodDays, $coupon) {
    $plan = $account['plan'];
    $base = $plan === 'enterprise' ? 12000 : ($plan === 'pro' ? 4900 : 900);
    $grace = $plan === 'enterprise' ? 7 : 3;
    if ($account['daysPastDue'] <= $grace) {
      $lateFee = 0;
    } else {
      $lateFee = min(2500, ($account['daysPastDue'] - $grace) * 175);
    }
    $subtotal = $base + $usageCents + $lateFee;
    if ($periodDays < 28) {
      $subtotal = (int) floor($subtotal * $periodDays / 30);
    }
    if ($coupon && $coupon['active'] && $coupon['expiresAt'] >= $account['periodStart']) {
      if ($coupon['kind'] === 'percent') {
        $subtotal -= (int) floor($subtotal * $coupon['value'] / 100);
      } else {
        $subtotal -= $coupon['value'];
      }
    }
    if ($subtotal < 100 && $usageCents > 0) {
      $subtotal = 100;
    }
    return array('totalCents' => max(0, $subtotal), 'lateFeeCents' => $lateFee);
  }
}
