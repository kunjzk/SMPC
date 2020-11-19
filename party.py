# Tharusha Amarasinghe TA2617
# Kunal Katarya KK3415

from circuit import ALL_PARTIES, DEGREE, N_GATES, GATES
import log
import circuit
import modprime


############################# HELPER FUNCTIONS #################################
def gen_coeffs(priv_value):
  '''
  Generates list of random coefficients which correspond to degrees of a
  polynomial, up to degree = DEGREE.

  List format is [priv_value, a, b, ..]
  for polynomial: priv_value + ax + bx^2 + ...
  '''
  if DEGREE < 1:
    raise Exception("[ERROR] Invalid degree value: %d" % DEGREE)
  log.debug("degree %d" % DEGREE)
  randnums = [modprime.randint() for _ in range(DEGREE)]
  coeffs= [priv_value]
  coeffs += randnums
  return coeffs


def create_share(coeffs: object, x: object) -> object:
  '''
  Returns P(x) mod PRIME.

  where P(x) = coeffs[0] + coeffs[1]*x + coeffs[2]*x^2 + ...
  '''
  evals = []
  for deg, co in enumerate(coeffs, start=0):
    evals.append(co*(x**deg))
  res = sum(evals)
  log.debug("[SHARECREATE] evals = %s" % evals)
  log.debug("[SHARECREATE] Poly res = %d mod prime -> %d" % (res,  modprime.mod(res)))
  return modprime.mod(res)


def interpolate(received_values, final=False):
  '''
  Perform lagrange interpolation to recover secret value from received_values.
  '''
  upper_bound = DEGREE+2 if final else 2*DEGREE+2
  recomb = []
  for i in range(1, upper_bound):
    prod = 1
    for j in range(1, upper_bound):
      if j != i:
        prod = prod * (j/(j-i))
    recomb.append(int(prod))
  log.debug("[INTER] recomb vector = %s" % recomb)
  res = 0
  for i, vec in enumerate(recomb, start=0):
    res += vec*received_values[i]
  return modprime.mod(res)


def create_and_send_shares(src_gate, polynomial, network):
    '''
    Create and send a share to each party based on a polynomial.

    src_gate: gate of agent for which share is being sent.
    '''
    sent_shares = []
    for dest_party in ALL_PARTIES:
      share = create_share(polynomial, dest_party)
      sent_shares.append(share)
      log.debug("[SHARESEND] Sending share %d for gate %d to party_no %d" % \
        (share, src_gate, dest_party))
      network.send_share(share, src_gate, dest_party)
    log.write("[SHARESEND] Sent shares %s" % sent_shares)


def receive_shares(src_gate, network):
    '''
    Receives and returns shares for the current gate from all parties.
    '''
    received_shares = []
    for party in ALL_PARTIES:
        received_shares.append(network.receive_share(party, src_gate))
    return received_shares


def send_final_value(final_value, final_gate, network):
    '''
    Shares final_value to each final_gate of all parties.
    '''
    for party in ALL_PARTIES:
        network.send_share(final_value, final_gate, party)


def degree_reduction(needs_reduction_res, curr_gate, network):
    '''
    Wrapper function to perform degree reduction.

    Returns interpolated value.
    '''
    # Create new polynomial, create shares and send them to all parties
    deg_red_coeffs = gen_coeffs(needs_reduction_res)
    log.debug("[DEGRED] coeffs %s" % deg_red_coeffs)
    create_and_send_shares(curr_gate, deg_red_coeffs, network)

    # Get shares sent from all parties, and interpolate to get new output
    received_shares = receive_shares(curr_gate, network)
    log.write("[DEGRED] received shares %s" % receive_shares)
    res = interpolate(received_shares, final=False)
    log.write("[DEGRED] interpolated output of gate %d: %d" %\
       (curr_gate, res))
    return res


################################## GATES #######################################
def input_gate(gate_inputs, curr_gate, next_gate, input_no, network):
    '''
    Receive a share for the current gate from the corresponding party.
    '''
    share = network.receive_share(curr_gate, curr_gate)
    if input_no == 1:
      gate_inputs[next_gate] = [share]
    else:
      gate_inputs[next_gate].append(share)


def add_gate(gate_inputs, curr_gate, next_gate, input_no):
    '''
    Add two inputs, store result in gate_inputs
    '''
    if (len(gate_inputs[curr_gate]) != 2):
      raise Exception("[ADD][ERROR] Incorrect number of inputs: %d" % \
        len(gate_inputs[curr_gate]))
    op1,op2 = gate_inputs[curr_gate]
    res = modprime.add(op1,op2)
    log.write("[ADD] Performing (%d + %d) mod prime = %d" % (op1, op2, res))
    if input_no == 1:
      gate_inputs[next_gate] = [res]
    else:
      gate_inputs[next_gate].append(res)


def mul_gate(gate_inputs, curr_gate, next_gate, input_no, network):
    '''
    Multiply two inputs, perform degree reduciton via secret sharing and
    interpolation, store result in gate_inputs
    '''
    if (len(gate_inputs[curr_gate]) != 2):
      raise Exception("[MUL][ERROR] Incorrect number of inputs: %d" % \
        len(gate_inputs[curr_gate]))

    op1,op2 = gate_inputs[curr_gate]
    needs_reduction_res = modprime.mul(op1,op2)
    log.write("[MUL] Performing (%d * %d) mod prime = %d" % \
      (op1, op2, needs_reduction_res))
    res = degree_reduction(needs_reduction_res, curr_gate, network)
    if input_no == 1:
      gate_inputs[next_gate] = [res]
    else:
      gate_inputs[next_gate].append(res)


def output_gate(gate_inputs, final_gate, network):
    '''
    Perform shamir secret sharing for the final value of this party's circuit
    '''
    if len(gate_inputs[final_gate]) != 1:
      raise Exception("[FINAL][ERROR] Incorrect number of inputs: %d" % \
        len(gate_inputs[final_gate]))

    final_value = gate_inputs[final_gate][0]
    log.debug("[FINAL] Sending final value %d all parties" % \
      (gate_inputs[final_gate][0]))
    send_final_value(final_value, final_gate, network)

    final_shares = receive_shares(final_gate, network)
    log.write("[FINAL] Final received shares %s" % final_shares)
    final_result = interpolate(final_shares, final=True)

    return final_result


################################## BGW  ########################################
def bgw_protocol(party_no, priv_value, network):
  '''
  Wrapper function that implements the skeleton of the BGW protocol.
  '''
  log.debug("[INIT] Private value: %d, party no %d" % (priv_value, party_no))

  # A dict that holds the inputs to each gate.
  # Add/Mul gates have 2 inputs (list), Input gates have just 1.
  gate_inputs = {}

  # Generate initial random polynomial coefficients with private value
  coeffs = gen_coeffs(priv_value)
  log.debug("[INIT] Polynomial Coeffs: %s" % coeffs)

  # Create share of private value using polynomial, send to all parties
  create_and_send_shares(party_no, coeffs, network)

  # Evaluate each gate in circuit, depending on gate type
  for curr_gate in GATES:
    gate_type, next_gate, input_no = GATES[curr_gate]
    log.write("[GATE]: %d, %s" % (curr_gate,\
      ("MUL"if gate_type==2 else ("ADD" if gate_type==1 else "INP"))))

    if (gate_type == circuit.INP):
      input_gate(gate_inputs, curr_gate, next_gate, input_no, network)
    elif (gate_type == circuit.ADD):
      add_gate(gate_inputs, curr_gate, next_gate, input_no)
    elif (gate_type == circuit.MUL):
      mul_gate(gate_inputs, curr_gate, next_gate, input_no, network)
    else:
      raise Exception("Unsupported gate type number: %d" % gate_type)

  # Evaluate output gate (output of last circuit gate)
  final_gate = N_GATES+1
  final_result = output_gate(gate_inputs, final_gate, network)
  log.write("[FINAL] Our Result: %d, Function Result %d" % (final_result,\
    circuit.function(circuit.PRIVATE_VALUES)))