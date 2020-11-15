# Tharusha Amarasinghe TA2617
# Kunal Katarya KK__17


from circuit import ALL_PARTIES, DEGREE, N_GATES, PRIVATE_VALUES, GATES
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

def poly_prime(coeffs, x):
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

def recombine(final_values):
  # coords = {}
  # log.debug("Recombining final values %s" % final_values)
  # for x,y in enumerate(final_values, start=1):
  #   log.write("x: %d, y: %d" % (x,y))
  #   coords[x] = y

  # # no_of_coords = DEGREE + 1
  # delta_zeros = {}
  # # Compute the function on each set
  # for x,y in coords.items():
    
  #   num = 1
  #   dom = 1
  #   for i in range(DEGREE):
  #     # Pick coordinates that arent the current one
  #     num =  num * (x+1+i)
  #     dom =  dom * 2
  #   delta_zeros[x] = (num/dom)

  #   if len(delta_zeros) == DEGREE + 1:
  #     break
  
  
  # res = 0
  # for x in delta_zeros:
  #   log.write("delta=%d * y=%d = %d" % (delta_zeros[x],coords[x],delta_zeros[x] * coords[x]))
  #   res += delta_zeros[x] * coords[x]

  # Make recomb vector, using formula from bottom of slide 26
  recomb = []
  for i in range (1, DEGREE+2):
    prod = 1
    for j in range(1,DEGREE+2):
      if j != i:
        prod = prod * (j/(j-i))
    recomb.append(prod)
  log.write("recomb vector = %s" % recomb)

  res = 0
  # Compute result using recombination vector and final values
  for i, vec in enumerate(recomb, start=0):
    res += vec*final_values[i]

  log.write("Final result -> Ours: %d, actual %d" % (modprime.mod(res), circuit.function(circuit.PRIVATE_VALUES)))
  



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
      share = network.receive_share(cur_wire, cur_wire)
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
      log.debug("Performing %d + %d = %d" % (op1, op2, res))
      if input_no == 1:
        gate_inputs[out_wire] = [res]
      else:
        gate_inputs[out_wire].append(res)
    

    elif (g_type == circuit.MUL):
      if (len(gate_inputs[cur_wire]) != 2):
        log.write("[WARNING] Incorrect number of inputs: %d" % len(gate_inputs[cur_wire]))
      op1,op2 = gate_inputs[cur_wire]
      log.debug("Performing %d * %d" % (op1, op2))
      res = op1 * op2
      # TODO need to do degree reduction

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

  recombine(final_values)
  