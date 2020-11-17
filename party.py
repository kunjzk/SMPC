# Tharusha Amarasinghe TA2617
# Kunal Katarya KK3415


from circuit import ALL_PARTIES, DEGREE, N_GATES, PRIME, PRIVATE_VALUES, GATES
import log
import circuit
import modprime

def gen_coeffs(priv_value):
  if DEGREE < 1:
    log.write("[WARNING] Invalid degree value: %d" % DEGREE)
  log.debug("degree %d" % DEGREE)
  randnums = [modprime.randint() for _ in range(DEGREE)]
  coeffs= [priv_value]
  coeffs += randnums

  # log.debug(coeffs)
  return coeffs

def poly_prime(coeffs: object, x: object) -> object:
  ''' Retuns P(x) mod PRIME '''
  evals = []
  for deg, co in enumerate(coeffs, start=0):
    log.debug("deg: %d, co: %d" % (deg,co))
    # res += co*(x**deg)
    evals.append(co*(x**deg))
  res = sum(evals)
  log.write("evals = %s" % evals)
  log.write("poly res = %d -> %d" % (res,  modprime.mod(res)))
  return modprime.mod(res)

def recombine(received_values, final=False):
  # Make recomb vector, using formula from bottom of slide 26
  upper_bound = DEGREE+2 if final else 2*DEGREE+2
  recomb = []
  for i in range(1, upper_bound):
    prod = 1
    for j in range(1, upper_bound):
      if j != i:
        prod = prod * (j/(j-i))
    recomb.append(int(prod))
  log.write("recomb vector = %s" % recomb)

  res = 0
  # Compute result using recombination vector and final values
  for i, vec in enumerate(recomb, start=0):
    res += vec*received_values[i]

  if final: log.write("Final result -> Ours: %d, actual %d" % (modprime.mod(res),\
     circuit.function(circuit.PRIVATE_VALUES)))

  return modprime.mod(res)



def bgw_protocol(party_no, priv_value, network):
  # network is pointer to network instantiation for agent_no
  log.debug("Called bgw protocol!")
  log.debug("Private value: %d, party no %d" % (priv_value, party_no))

  # Every add/mull has 2 inputs that need to be filled (input 1 and 2)
  # whilst input gates require 1 input
  # gates are a 3-tuple of gate_type, eval_level, inp_no, where eval_level is
  # the evaluation stage that it the result of the cur_wire will be used, and
  # inp_no is the input number for that gate it will be used for
  gate_inputs = {}



  # for gate_no in GATES:
  #   g_type,out_gate,inputs = GATES[gate_no]
  #   if g_type == circuit.INP:
  #     gate_inputs[]
  # Create shares
  coeffs = gen_coeffs(priv_value)
  log.debug("Coeffs: %s" % coeffs)

  # Send shares
  for party in ALL_PARTIES:
    share = poly_prime(coeffs, party)
    wire = party_no
    log.write("Sending share %d for wire %d to party_no %d" % (share, wire, party))
    network.send_share(share, wire, party)

  # For each wire (output from the gate), wait for shares
  for cur_wire in GATES:

    g_type,out_wire,input_no = GATES[cur_wire]
    log.write("[WIRE]: %d, %s" % (cur_wire, g_type))

    if (g_type == circuit.INP):
      log.debug("Input gate, Receiving shares.")
      share = network.receive_share(cur_wire, cur_wire)
      log.debug("Received share %d" % share)
      # Create and send share
      if input_no == 1:
        gate_inputs[out_wire] = [share]
      else:
        gate_inputs[out_wire].append(share)


    elif (g_type == circuit.ADD):
      if (len(gate_inputs[cur_wire]) != 2):
        log.write("[WARNING] Incorrect number of inputs: %d" % len(gate_inputs[cur_wire]))
      op1,op2 = gate_inputs[cur_wire]
      res = modprime.add(op1,op2)
      log.debug("Performing (%d + %d) mod prime = %d" % (op1, op2, res))
      if input_no == 1:
        gate_inputs[out_wire] = [res]
      else:
        gate_inputs[out_wire].append(res)


    elif (g_type == circuit.MUL):
      if (len(gate_inputs[cur_wire]) != 2):
        log.write("[WARNING] Incorrect number of inputs: %d" % len(gate_inputs[cur_wire]))
      op1,op2 = gate_inputs[cur_wire]
      res = modprime.mul(op1,op2)
      log.write("Performing (%d * %d) mod prime = %d" % (op1, op2, res))

      # first, create a random polynomial of the original degree. Constant = res.
      deg_red_coeffs = gen_coeffs(res)

      received_shares = []
      for party in ALL_PARTIES:
        share = poly_prime(deg_red_coeffs, party)
        network.send_share(share, cur_wire, party)
        log.write("Sending share %d for wire %d to party_no %d" % (share, cur_wire, party))
        received_shares.append(network.receive_share(party, cur_wire))
      res = recombine(received_shares, final=False)
      log.write("Recombined output of gate %d: %d" % (cur_wire, res))
      if input_no == 1:
        gate_inputs[out_wire] = [res]
      else:
        gate_inputs[out_wire].append(res)

  final_wire = N_GATES+1

  # log.debug("final indx = %d" % final_wire)
  if len(gate_inputs[final_wire]) != 1:
    log.write("[WARNING] Incorrect number of inputs: %d" % len(gate_inputs[final_wire]))
  log.debug("Sending final value %d all parties" % (gate_inputs[final_wire][0]))

  final_values = []
  # Send shares of final value
  for party in ALL_PARTIES:
    network.send_share(gate_inputs[final_wire][0], final_wire, party)

    # Get share from parties
    final_values.append(network.receive_share(party, final_wire))

  final_result = recombine(final_values, final=True)
