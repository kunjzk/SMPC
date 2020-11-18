# Tharusha Amarasinghe TA2617
# Kunal Katarya KK3415

from circuit import ALL_PARTIES, DEGREE, N_GATES, PRIME, PRIVATE_VALUES, GATES
import log
import circuit
import modprime

def gen_coeffs(priv_value):
  '''Generate random polynomial (degree = DEGREE) where constant=secret'''
  if DEGREE < 1:
    log.write("[WARNING] Invalid degree value: %d" % DEGREE)
  log.debug("degree %d" % DEGREE)
  randnums = [modprime.randint() for _ in range(DEGREE)]
  coeffs= [priv_value]
  coeffs += randnums
  return coeffs

def create_share(coeffs: object, x: object) -> object:
  ''' Retuns P(x) mod PRIME '''
  evals = []
  for deg, co in enumerate(coeffs, start=0):
    evals.append(co*(x**deg))
  res = sum(evals)
  log.write("evals = %s" % evals)
  log.write("poly res = %d -> %d" % (res,  modprime.mod(res)))
  return modprime.mod(res)

def interpolate(received_values, final=False):
  '''Perform lagrange interpolation to recover secret'''
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
  for i, vec in enumerate(recomb, start=0):
    res += vec*received_values[i]
  if final: log.write("Final result -> Ours: %d, actual %d" % (modprime.mod(res),\
     circuit.function(circuit.PRIVATE_VALUES)))
  return modprime.mod(res)

def output_gate(gate_inputs, final_gate, network):
    if len(gate_inputs[final_gate]) != 1:
      log.write("[WARNING] Incorrect number of inputs: %d" % len(gate_inputs[final_gate]))
    final_value = gate_inputs[final_gate][0]
    log.debug("Sending final value %d all parties" % (gate_inputs[final_gate][0]))
    send_final_value(final_value, final_gate, network)
    final_shares = receive_shares(final_gate, network)
    log.write("Final shares %s" % final_shares)
    final_result = interpolate(final_shares, final=True)

def create_and_send_shares(src_gate, polynomial, network):
    '''Create and send a share to each party based on a polynomial'''
    sent_shares = []
    for dest_party in ALL_PARTIES:
      share = create_share(polynomial, dest_party)
      sent_shares.append(share)
      log.debug("Sending share %d for wire %d to party_no %d" % (share, src_gate, dest_party))
      network.send_share(share, src_gate, dest_party)
    log.write("Sent shares %s" % sent_shares)

def receive_shares(src_gate, network):
    '''Receive shares for the current gate from all parties'''
    received_shares = []
    for party in ALL_PARTIES:
        received_shares.append(network.receive_share(party, src_gate))
    return received_shares

def send_final_value(final_value, final_gate, network):
    '''Share final output with all other parties'''
    for party in ALL_PARTIES:
        network.send_share(final_value, final_gate, party)

def degree_reduction(needs_reduction_res, curr_gate, network):
    '''Wrapper function to perform degree reduction'''
    deg_red_coeffs = gen_coeffs(needs_reduction_res)
    log.write("Degree reduction coeffs %s" % deg_red_coeffs)
    create_and_send_shares(curr_gate, deg_red_coeffs, network)
    received_shares = receive_shares(curr_gate, network)
    res = interpolate(received_shares, final=False)
    log.write("interpolated output of gate %d: %d" % (curr_gate, res))
    return res

def add_gate(gate_inputs, curr_gate, next_gate, input_no):
    '''Add two inputs, store result'''
    if (len(gate_inputs[curr_gate]) != 2):
      log.write("[WARNING] Incorrect number of inputs: %d" % len(gate_inputs[curr_gate]))
    op1,op2 = gate_inputs[curr_gate]
    res = modprime.add(op1,op2)
    log.debug("Performing (%d + %d) mod prime = %d" % (op1, op2, res))
    if input_no == 1:
      gate_inputs[next_gate] = [res]
    else:
      gate_inputs[next_gate].append(res)

def mul_gate(gate_inputs, curr_gate, next_gate, input_no, network):
    '''
    Multiply two inputs, perform secret sharing and interpolation, store result
    '''
    if (len(gate_inputs[curr_gate]) != 2):
      log.write("[WARNING] Incorrect number of inputs: %d" % len(gate_inputs[curr_gate]))
    op1,op2 = gate_inputs[curr_gate]
    needs_reduction_res = modprime.mul(op1,op2)
    log.write("Performing (%d * %d) mod prime = %d" % (op1, op2, needs_reduction_res))
    res = degree_reduction(needs_reduction_res, curr_gate, network)
    if input_no == 1:
      gate_inputs[next_gate] = [res]
    else:
      gate_inputs[next_gate].append(res)

def input_gate(gate_inputs, curr_gate, next_gate, input_no, network):
    '''Receive a share for the current gate from the corresponding party'''
    share = network.receive_share(curr_gate, curr_gate)
    if input_no == 1:
      gate_inputs[next_gate] = [share]
    else:
      gate_inputs[next_gate].append(share)

def bgw_protocol(party_no, priv_value, network):
  log.debug("Called bgw protocol!")
  log.debug("Private value: %d, party no %d" % (priv_value, party_no))

  # A dict that holds the inputs to each gate.
  # Add/Mul gates have 2 inputs, Input gates have just 1.
  gate_inputs = {}

  coeffs = gen_coeffs(priv_value)
  log.debug("Polynomial Coeffs: %s" % coeffs)
  create_and_send_shares(party_no, coeffs, network)

  for curr_gate in GATES:
    gate_type, next_gate, input_no = GATES[curr_gate]
    log.write("[WIRE]: %d, %s" % (curr_gate, gate_type))

    if (gate_type == circuit.INP):
      input_gate(gate_inputs, curr_gate, next_gate, input_no, network)

    elif (gate_type == circuit.ADD):
        add_gate(gate_inputs, curr_gate, next_gate, input_no)

    elif (gate_type == circuit.MUL):
        mul_gate(gate_inputs, curr_gate, next_gate, input_no, network)

  final_gate = N_GATES+1
  final_result = output_gate(gate_inputs, final_gate, network)
