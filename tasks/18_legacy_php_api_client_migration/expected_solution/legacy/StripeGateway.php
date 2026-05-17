<?php
class StripeGateway {
  public function charge($stripe, $request) {
    $params = array(
      'amount' => $request['amountCents'],
      'currency' => strtolower($request['currency']),
      'customer' => $request['customerId'],
      'metadata' => array_merge($request['metadata'], array('order_id' => $request['orderId']))
    );
    $opts = array('idempotency_key' => 'charge:' . $request['orderId'] . ':' . $request['attempt']);
    try {
      $charge = $stripe->charges->create($params, $opts);
      return array('ok' => true, 'chargeId' => $charge->id, 'recoverable' => false);
    } catch (CardException $e) {
      return array('ok' => false, 'chargeId' => null, 'recoverable' => $e->getDeclineCode() === 'insufficient_funds');
    }
  }
}
