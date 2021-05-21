import os
import sys

lineNumber = 1

def generateExitCode():
    # Generate exit code
    s = []
    
    s.append('(EXIT)')
    s.append('@EXIT')
    s.append('0;JMP')

    return s

def generatePushCode(segment, index):
    # Push value into the stack
    s = [] 

    if segment == 'constant':        
        s.append('@' + index)
        s.append('D=A')
    elif segment == 'temp':              
        s.append('@' + str(5 + int(index))) 
        s.append('D=M') 
    elif segment == 'pointer':      
        s.append('@' + str(3 + int(index)))   
        s.append('D=M')    
    elif segment == 'static':              
        s.append('@' + segment + '.' + index)   
        s.append('D=M')  
    else:
        s.append('@' + index)
        s.append('D=A')
        if segment == 'local':
            s.append('@LCL') 
        elif segment == 'argument':
            s.append('@ARG') 
        elif segment == 'this':
            s.append('@THIS')
        elif segment == 'that': 
            s.append('@THAT')  
        else:
            s = []
            return s
        s.append('A=D+M')
        s.append('D=M') 
    
    s.append('@SP')
    s.append('A=M')
    s.append('M=D')
    s.append('@SP')
    s.append('M=M+1')

    return s
    
def generatePopCode(segment, index):
    # Code to pop value from the stack
    s = []

    if segment == 'temp':              
        s.append('@' + str(5 + int(index)))  
    elif segment == 'pointer':      
        s.append('@' + str(3 + int(index)))   
    elif segment == 'static':  
        s.append('@' + segment + '.' + index)   
    else:        
        s.append('@' + index)
        s.append('D=A')
        if segment == 'local':
            s.append('@LCL')
        elif segment == 'argument': 
            s.append('@ARG')
        elif segment == 'this':
            s.append('@THIS') 
        elif segment == 'that': 
            s.append('@THAT')
        else:
            s = []
            return s
        s.append('A=D+M')
    
    s.append('D=A')
    s.append('@R13')
    s.append('M=D')
    s.append('@SP')
    s.append('M=M-1')
    s.append('@SP')
    s.append('A=M')    
    s.append('D=M')
    s.append('@R13')
    s.append('A=M')
    s.append('M=D')

    return s

def generateArithmeticOrLogicCode(operation):
    # Code to perform specified ALU operation
    s = []
    
    s.append('@SP') 
    s.append('AM=M-1') 
    s.append('D=M')
    s.append('A=A-1') 

    if operation == 'add': 
        s.append('M=M+D')
    elif operation == 'sub': 
        s.append('M=M-D')
    elif operation == 'or': 
        s.append('M=M|D')
    elif operation == 'and': 
        s.append('M=M&D')
    else:
        s = []
        return s
    
    return s

def generateUnaryOperationCode(operation):
    # Code to perform specified unary operation
    s = []

    s.append('@SP')
    s.append('A=M-1')
    if operation == 'not':
        s.append('M=!M')
    elif operation == 'neg':
        s.append('M=-M')
    else:
        s = []
        return s

    return s

def generateRelationCode(operation, lineNumber):
    # Code to perform the specified relational operation
    s = []
    label_1 = ''
    label_2 = ''

    s.append('@SP')
    s.append('AM=M-1')
    s.append('D=M')
    s.append('A=A-1')           # Adjust stack pointer
    s.append('D=M-D')           # D = operand1 - operand2
        
    if operation == 'lt':
        label_1 = 'IF_LT_' + str(lineNumber)
        s.append('@' + label_1)
        s.append('D;JLT')       # if operand1 < operand2 goto IF_LT_*
    elif operation == 'eq':
        label_1 = 'IF_EQ_' + str(lineNumber)
        s.append('@' + label_1)
        s.append('D;JEQ')       # if operand1 = operand2 goto IF_EQ_*
    elif operation == 'gt':
        label_1 = 'IF_GT_' + str(lineNumber)
        s.append('@' + label_1)
        s.append('D;JGT')       # if operand1 > operand2 goto IF_GT_*
    else:
        s = []
        return s    

    s.append('D=0')          
    label_2 = 'END_IF_ELSE_' + str(lineNumber)
    s.append('@' + label_2)
    s.append('0;JMP')
    s.append('(' + label_1 + ')')
    s.append('D=-1')        
    s.append('(' + label_2 + ')')
    s.append('@SP')
    s.append('A=M-1')
    s.append('M=D')            # Save result on stack

    return s  

def generateIfGotoCode(label):
    # Code for the if-goto statement
    s = []

    s.append('@SP')
    s.append('M=M-1')
    s.append('A=M')
    s.append('D=M')
    s.append('@' + label)
    s.append('D;JNE')
    
    return s

def generateGotoCode(label):
    # Code for goto
    s = []

    s.append('@' + label)
    s.append('0;JMP')

    return s

def generatePseudoInstructionCode(label):   
    # Generate pseudo-instruction for label
    s = []
    
    s.append('(' + label + ')')

    return s

def generateSetCode(register, value):
    # Generate assembly code for set
    s = []
    
    s.append('@' + value)
    s.append('D=A')
    
    if register == 'sp':
        s.append('@SP')
    
    if register == 'local':
        s.append('@LCL')
    
    if register == 'argument':
        s.append('@ARG')
        
    if register == 'this':
        s.append('@THIS')
        
    if register == 'that':
        s.append('@THAT')
        
    s.append('M=D')
    
    return s

def generateFunctionCallCode(function, nargs, lineNumber):  
    # Generate preamble for function
    s = []
    
    s.append('@RET_' + function + '_' + str(lineNumber))
    s.append('D=A')
    s.append('@SP')
    s.append('A=M')
    s.append('M=D')
    s.append('@SP')
    s.append('M=M+1') 
    
    # Push LCL, ARG, THIS, and THAT registers to stack
    for reg in ['@LCL', '@ARG', '@THIS', '@THAT']:
        s.append(reg)
        s.append('D=M')
        s.append('@SP')
        s.append('A=M')
        s.append('M=D')
        s.append('@SP')
        s.append('M=M+1')
    
    # Set LCL register to current SP    
    s.append('@SP')
    s.append('D=M')
    s.append('@LCL')
    s.append('M=D') 

    # Set ARG register to point to start of arguments in the current frame
    s.append('@5')
    s.append('D=D-A')
    s.append('@' + nargs)
    s.append('D=D-A')
    s.append('@ARG')
    s.append('M=D') 
      
    # Generate goto code to jump to function
    s.append('@' + function)
    s.append('0;JMP')

    # Generate the pseudo-instruction/label corresponding to the return address
    s.append('(RET_' + function + '_' + str(lineNumber) + ')')
    
    return s

def generateFunctionBodyCode(f, nvars):
    # Generate code for function f
    s = []
    
    # Generate the pseudo instruction -- the label
    s.append('(' + f + ')')
    
    # Push nvars local variables into the stack, each intialized to zero''
    for _ in range(nvars):
        s.append('@SP')
        s.append('A=M')
        s.append('M=0')
        s.append('@SP')
        s.append('M=M+1')

    return s

def generateFunctionReturnCode():
    # Generate assembly code for function return

    s = []

    # Copy LCL to temp register R14 (FRAME)
    s.append('@LCL')
    s.append('D=M')
    s.append('@R14')
    s.append('M=D')
    
    # Store return address in temp register R15 (RET)
    s.append('D=M')  
    s.append('@5')
    s.append('A=D-A')
    s.append('D=M')
    s.append('@R15')
    s.append('M=D')
    
    # Pop result from the working stack and move it to beginning of ARG segment
    s.append('@SP')
    s.append('M=M-1')
    s.append('A=M')
    s.append('D=M')
    s.append('@ARG')
    s.append('A=M')
    s.append('M=D')

    # Adjust SP = ARG + 1
    s.append('@ARG')
    s.append('D=M')
    s.append('@SP')
    s.append('M=D+1')
    
    # Restore THAT = *(FRAME - 1)
    s.append('@R14')
    s.append('AM=M-1')
    s.append('D=M')
    s.append('@THAT')
    s.append('M=D')
    
    # Restore THIS = *(FRAME - 2)
    s.append('@R14')
    s.append('AM=M-1')
    s.append('D=M')
    s.append('@THIS')
    s.append('M=D')
    
    # Restore ARG = *(FRAME - 3)
    s.append('@R14')
    s.append('AM=M-1')
    s.append('D=M')
    s.append('@ARG')
    s.append('M=D')
    
    # Restore LCL = *(FRAME - 4)
    s.append('@R14')
    s.append('AM=M-1')
    s.append('D=M')
    s.append('@LCL')
    s.append('M=D')

    # Jump to return address stored in R15 back to the caller code    
    s.append('@R15')
    s.append('A=M')
    s.append('0;JMP')
   
    return s

def translateVmCommands(tokens, lineNumber):
    # Translate a VM command into corresponding Hack assembly commands
    s = []
    
    if tokens[0] == 'push':
        s = generatePushCode(tokens[1], tokens[2])    # Generate code to push into stack
        
    elif tokens[0] == 'pop':
        s = generatePopCode(tokens[1], tokens[2])     # Generate code to pop from stack
        
    elif tokens[0] == 'add' or tokens[0] == 'sub' \
         or tokens[0] == 'or' or tokens[0] == 'and':
        s = generateArithmeticOrLogicCode(tokens[0])  # Generate code for ALU operation
        
    elif tokens[0] == 'neg' or tokens[0] == 'not':
        s = generateUnaryOperationCode(tokens[0])     # Generate code for unary operations
        
    elif tokens[0] == 'eq' or tokens[0] == 'lt' or tokens[0] == 'gt':
        s = generateRelationCode(tokens[0], lineNumber)
    
    elif tokens[0] == 'label':
        s = generate_pseudo_instruction_code(tokens[1])
    
    elif tokens[0] == 'if-goto':
        s = generateIfGotoCode(tokens[1]) 
        
    elif tokens[0] == 'goto':
        s = generateGotoCode(tokens[1])
    
    elif tokens[0] == 'end':
        s = generateExitCode()
        
    elif tokens[0] == 'set':
        s = generateSetCode(tokens[1], tokens[2])
        
    elif tokens[0] == 'function':
        s = generateFunctionBodyCode(tokens[1], int(tokens[2]))
        
    elif tokens[0] == 'call':
        s = generateFunctionCallCode(tokens[1], tokens[2], lineNumber)
        
    elif tokens[0] == 'return':
        s = generateFunctionReturnCode()
        
    else:
        print('translateVmCommands: Unknown operation')           # Unknown operation 
    
    return s
    
def translateFile(inputFile):
    # Translate VM file to Hack assembly code
    global lineNumber
    assemblyCode = []
    assemblyCode.append('// ' + inputFile)
    
    with open(inputFile, 'r') as f:
        for command in f:        
            # print("Translating line:", lineNumber, command)
            tokens = (command.rstrip('\n')).split()
            
            if not tokens:
                continue                                        # Ignore blank lines  
            
            if tokens[0] == '//':
                continue                                        # Ignore comment       
            else:
                s = translateVmCommands(tokens, lineNumber)
                lineNumber = lineNumber + 1        
            if s:
                
                for i in s:
                    assemblyCode.append(i)
            else:
                return False
            
    # Write translated commands to .i file
    fileNameMinusExtension, _ = os.path.splitext(inputFile)
    outputFile = fileNameMinusExtension + '.i'
    out = open(outputFile, 'w')
    for s in assemblyCode:
        out.write('%s\n' %s)
    out.close()
    print('Assembly file generated: ', outputFile)
        
    return True

def runVmToAsmTranslator(path):
    # Main translator code"""
    files = os.listdir(path)
    
    cwd = os.getcwd()
    os.chdir(path)
    
    if 'sys.vm' in files:
        idx = files.index('sys.vm')
        f = files.pop(idx)
        print('Translating:', f)
        status = translateFile(f)
        if status == False:
            print('Error translating ', f)
            return False
    else:
        print('Missing sys.vm file')
        return False
        
    if 'main.vm' in files:
        idx = files.index('main.vm')
        f = files.pop(idx)
        print('Translating:', f)
        status = translateFile(f)
        if status == False:
            print('Error translating ', f)
            return False
    else:
        print('Missing main.vm file')
        return False
    
    for f in files:
        print('Translating:', f)
        status = translateFile(f)
        if status == False:
            print('Error translating ', f)
            return False
    
    os.chdir(cwd)
    
    return True

def assembleFinalFile(outputFile, path):
    # Assemble final output file
    intermediateFiles = []
    files = os.listdir(path)
    for f in files:
        if f.endswith('.i'):
            intermediateFiles.append(f)
            
    cwd = os.getcwd()
    os.chdir(path)
    
    with open(outputFile, 'w') as outfile:    
        idx = intermediateFiles.index('sys.i')
        f = intermediateFiles.pop(idx)
        with open(f, 'r') as infile:
            for line in infile:
                outfile.write(line)
                
        idx = intermediateFiles.index('main.i')
        f = intermediateFiles.pop(idx)
        with open(f, 'r') as infile:
            for line in infile:
                outfile.write(line)
        
        for f in intermediateFiles:
            with open(f, 'r') as infile:
                for line in infile:
                    outfile.write(line)

    os.chdir(cwd)
    return True
    
def cleanIntermediateFiles(path):
    # Removes intermediate .i files from supplied path
    intermediateFiles = []
    
    files = os.listdir(path)
    for f in files:
        if f.endswith('.i'):
            intermediateFiles.append(f)
            
    cwd = os.getcwd()
    os.chdir(path)
    
    for f in intermediateFiles:
        os.remove(f)
    
    os.chdir(cwd)

def cleanOldFiles(path):
    # Removes old files from supplied path
    oldFiles = []
    
    files = os.listdir(path)
    for f in files:
        if f.endswith('.asm') or f.endswith('.i') or f.endswith('.hack'):
            oldFiles.append(f)
            
    cwd = os.getcwd()
    os.chdir(path)
    
    for f in oldFiles:
        os.remove(f)
    
    os.chdir(cwd)
 
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: Python vm-translator.py file-name.asm path-name")
        print("file-name.asm: assembly file to be generated by the translator")
        print("path-name: directory containing .vm source files")
        print("Example: vm-translator.py mult-final.asm ./mult")
    else:
        outputFile = sys.argv[1]
        path = sys.argv[2]
        cleanOldFiles(path)
        
        status = runVmToAsmTranslator(path)

        if status == True:
            print('Intermediate assembly files were generated successfully')
            print('Generating final assembly file: ', outputFile)
            assembleFinalFile(outputFile, path)
            cleanIntermediateFiles(path)
        else:
            print('Error generating assembly code')