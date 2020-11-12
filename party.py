# Tharusha Amarasinghe TA2617
# Kunal Katarya KK__17

from circuit import DEGREE, PRIVATE_VALUES
import log
import circuit
import modprime

def gen_coeffs(priv_value):
  if DEGREE < 1:
    log.write("Invalid degree value: %d" % DEGREE)
  log.debug("degree %d" % DEGREE)
  randnums = [modprime.randint() for _ in range(DEGREE)]
  coeffs= [priv_value]
  coeffs += randnums

  # log.debug(coeffs)
  return coeffs

def poly_prime(coeffs, x):
  ''' Retuns P(x) mod PRIME '''
  res = 0
  for deg, co in enumerate(coeffs, start=1):
    # log.debug("deg: %d, co: %d" % (deg,co))
    # print(co)
    res += co*(x**(deg))
  return modprime.mod(res)


def bgw_protocol(party_no, priv_value, network):
  # network is pointer to network instantiation for agent_no
  log.debug("Called bgw protocol!")
  log.debug("Private value: %d, party no %d" % (priv_value, party_no))

  # Create shares
  coeffs = gen_coeffs(priv_value)

  # Send shares
  for no in PRIVATE_VALUES:
    share = poly_prime(coeffs, no)
    # TODO determine which gate to send to
    gate = 0
    log.debug("Sending share %d for gate %d to dest_no %d" % (share, gate, no))
    network.send_share(share, gate, no)