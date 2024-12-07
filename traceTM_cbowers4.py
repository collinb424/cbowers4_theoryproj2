import csv, sys
from collections import deque

class Node:
    def __init__(self, past, curr_state, future, parent, children=None):
        self.past = past
        self.curr_state = curr_state
        self.future = future
        self.parent = parent
        self.children = children if children is not None else []


def compute_nondeterminism(breadth_first_paths):
    """
    Compute the degree of nondeterminism based on the method provided in the project document
    """

    root = breadth_first_paths[0][0]
    num_outgoing_transitions = 0
    num_nonleaves = 0
    queue = deque([root])

    # Do a depth-first traversal of the tree created in the `trace_with_node` function
    while queue:
        node = queue.popleft()

        if len(node.children) > 0:
            num_outgoing_transitions += len(node.children)
            num_nonleaves += 1

        for child in node.children:
            queue.append(child)

    return num_outgoing_transitions / num_nonleaves


def common_output(ntm, input_string, breadth_first_paths):
    """
    Print the output that all runs should echo, whether they accept, reject, or terminate
    """

    print(f"Name of machine: {ntm['name']}")
    print(f"Initial string: {input_string}")
    print(f"Depth of the tree of configurations: {len(breadth_first_paths) - 1}")

    # Count the number of transitions in breadth_first_paths
    total_num_transitions = sum(len(level) for level in breadth_first_paths) - 1
    print(f"Total number of transitions simulated: {total_num_transitions}" )

    print(f"Degree of nondeterminism: {compute_nondeterminism(breadth_first_paths)}")
    print()


def accepted_output(ntm, input_string, breadth_first_paths, accepting_path):
    """
    Report that the string was accepted and print its path from start to end
    """
    common_output(ntm, input_string, breadth_first_paths)

    print(f"String accepted in {len(accepting_path) - 1} transitions")
    print("Path of configurations from start to end:")
    for config in accepting_path:
        print(config)
    

def rejected_output(ntm, input_string, breadth_first_paths):
    """
    Print that the string was rejected and report the depth from the start to the last reject
    """
    common_output(ntm, input_string, breadth_first_paths)

    print(f"String rejected in {len(breadth_first_paths) - 1} transitions (i.e., the depth from the start to the last reject)")


def step_limit_exceeded_output(ntm, input_string, breadth_first_paths, termination):
    """
    Report that the execution was stopped
    """

    common_output(ntm, input_string, breadth_first_paths)

    print(f"Execution stopped because the depth of the configuration tree exceeded the specified limit of {termination}")


def generate_accepting_path(node):
    """
    Given an accepting node, use the parent attribute to retrace its path to the starting configuration
    """

    path = []
    while node is not None:
        path.append([node.past, node.curr_state, node.future])
        node = node.parent
    return path[::-1]


def trace_with_node(ntm, input_string, termination):
    """
    Simulates the trace of a nondeterministic Turing machine using breadth-first search.
    """

    # Create the root node based on the input string and starting state
    root = Node("", ntm['start'], input_string, None)
    queue = deque([root]) 
    breadth_first_paths = []

    # While the queue is nonempty, we continue our breadth-first traversal
    while queue:
        level_size = len(queue)
        curr_level = []

        # If the current depth exceeds the specified limit, stop the execution
        if len(breadth_first_paths) > termination:
            step_limit_exceeded_output(ntm, input_string, breadth_first_paths, termination)
            return

        # Iterate over all configurations on the current level of the tree
        for _ in range(level_size):
            node = queue.popleft()
            # Current level list is used to keep track of the configurations on a given level
            curr_level.append(node)
            past, curr_state, future = node.past, node.curr_state, node.future

            # Reached the accept state, so stop execution and print out the desired information
            if curr_state == ntm['accept']:
                breadth_first_paths.append(curr_level)
                accepting_path = generate_accepting_path(node)
                accepted_output(ntm, input_string, breadth_first_paths, accepting_path)
                return

            # Reached a reject state, so we want to move on to the next state
            if curr_state == ntm['reject']:
                continue

            # Add a blank character to mimic an infinite tape to the right
            if len(future) == 0:
                future += '_'

            # Not a valid transition in the NTM and leads to a reject state
            if (curr_state, future[0]) not in ntm:
                next_node = Node(past + future[0], ntm['reject'], future[1:], node)
                node.children.append(next_node)
                queue.append(next_node)
                continue
            
            # Iterate over the specified NTM transitions in the dictionary based
            # on the current state and next character
            for transition in ntm[(curr_state, future[0])]:
                new_state, new_char, dir = transition

                # Handle how the past and future parts of the configuration should be
                # updated based on if the direction is right or left
                if dir == 'R':
                    new_past = past + new_char
                    new_future = future[1:]
                elif dir == 'L':
                    new_past = past[:-1] # gets all characters except last
                    new_future = new_char + future[1:]
                    new_future = past[-1] + new_future if len(past) != 0 else new_future

                # Create a new node and add it to the queue to explore later
                next_node = Node(new_past, new_state, new_future, node)
                node.children.append(next_node)
                queue.append(next_node)
        
        # Done exploring the current level
        breadth_first_paths.append(curr_level)

    # If we have reached this point, that means we didn't hit an accept state or surpass
    # the specified depth limit, so this input must have been rejected
    rejected_output(ntm, input_string, breadth_first_paths)


def read_data(file_name="check_cbowers4.csv"):
    """
    Read the NTM from the specified CSV file
    """

    with open(file_name, mode='r', encoding='utf-8-sig') as file:
        csv_file = csv.reader(file)
        ntm = dict()

        for i, line in enumerate(csv_file):
            if i == 0:
                ntm['name'] = line[0]
            elif i == 4:
                ntm['start'] = line[0]
            elif i == 5:
                ntm['accept'] = line[0]
            elif i == 6:
                ntm['reject'] = line[0]
            elif i >= 7: # Parse the transitions of the NTM
                q_curr, char_input, q_new, char_new, dir_new = line

                # Add the specified transition to the dictionary
                if (q_curr, char_input) not in ntm:
                    ntm[(q_curr, char_input)] = [(q_new, char_new, dir_new)]
                else:
                    ntm[(q_curr, char_input)].append((q_new, char_new, dir_new))

    return ntm


def incorrect_arguments():
    """
    Provides error message when the user enters incorrect arguments.
    """

    print(
            '''
            Usage: python script_name.py <csv_file> <input_string> <termination_limit>
                   <csv_file>         Path to the CSV file defining the NTM.
                   <input_string>     The input string to process.
                   <termination_limit> Maximum depth for the configuration tree (integer).
            '''
        )
    sys.exit(1)


def parse():
    """
    Parses command-line arguments and provides detailed error messages
    when usage is incorrect.
    """

    args = sys.argv

    if len(args) != 4:
        incorrect_arguments()
        
    # Read the arguments
    try:
        script_name = args[1]
        input_string = args[2]
        termination = int(args[3])
    except:
        incorrect_arguments()

    # Generate the nondeterministic Turing Machine from the CSV file
    ntm = read_data(script_name)

    # Do a trace of the nondeterministic Turing machine using breadth-first search
    # based on the given input. Then report the results to the user
    trace_with_node(ntm, input_string, termination)

parse()