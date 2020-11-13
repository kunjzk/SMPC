# Tharusha Amarasinghe TA2617
# Kunal Katarya KK__17

from circuit import ALL_PARTIES, DEGREE, PRIVATE_VALUES
import log
import circuit
import modprime

def gen_coeffs(priv_value):
  if circuit.DEGREE < 1:
    log.write("[WARNING] Invalid degree value: %d" % circuit.DEGREE)
  log.debug("degree %d" % circuit.DEGREE)
  randnums = [modprime.randint() for _ in range(circuit.DEGREE)]
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

# def create_and_send_shares()


def bgw_protocol(party_no, priv_value, network):
  # network is pointer to network instantiation for agent_no
  log.debug("Called bgw protocol!")
  log.debug("Private value: %d, party no %d" % (priv_value, party_no))

  # Every add/mull has 2 inputs that need to be filled (input 1 and 2)
  # whilst input gates require 1 input
  # gates are a 3-tuple of gate_type, eval_level, inp_no, where eval_level is
  # the evaluation stage that it the result of the gate will be used, and
  # inp_no is the input number for that gate it will be used for
  gate_inputs = {}

  

  # for gate_no in circuit.GATES:
  #   g_type,out_gate,inputs = circuit.GATES[gate_no]
  #   if g_type == circuit.INP:
  #     gate_inputs[]
  # Create shares
  coeffs = gen_coeffs(priv_value)

  # Send shares
  for party in circuit.ALL_PARTIES:
    share = poly_prime(coeffs, party)
    gate = party_no
    log.debug("Sending share %d for gate %d to party_no %d" % (share, gate, party))
    network.send_share(share, gate, party)
    
  # For each gate, wait for shares
  for gate in circuit.GATES:
    # if gate not in circuit.ALL_PARTIES: break
    if gate == 10: break

    g_type,eval_lvl,input_no = circuit.GATES[gate]
    log.write("[GATE]: %d, %s" % (gate, g_type))

    if (g_type == circuit.INP):
      share = network.receive_share(gate, gate)
      # Create and send share
      if input_no == 1:
        gate_inputs[eval_lvl] = [share]
      else:
        gate_inputs[eval_lvl].append(share)
          

    elif (g_type == circuit.ADD):
      if (gate_inputs[gate] != 2):
        log.write("[WARNING] Incorrect number of inputs: %d" % len(gate_inputs[gate]))
      op1,op2 = gate_inputs[gate]
      log.debug("Performing %d + %d" % (op1, op2))
      res = op1 + op2
      if input_no == 1:
        gate_inputs[eval_lvl] = [res]
      else:
        gate_inputs[eval_lvl].append(res)
    

    elif (g_type == circuit.MUL):
      if (len(gate_inputs[gate]) != 2):
        log.write("[WARNING] Incorrect number of inputs: %d" % len(gate_inputs[gate]))
      op1,op2 = gate_inputs[gate]
      log.debug("Performing %d * %d" % (op1, op2))
      res = op1 * op2
      # TODO need to do degree reduction

      
  