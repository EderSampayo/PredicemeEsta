# Precision: TP/(TP+FP)
           # De todas las instancias que ha predecido como positive, realmente cuantas son 
# Recall: TP/(TP+FN)
           # De todos los positivos en realidad, cuantos hemos detectado bien
# F-score: 2*(P*R)/(P+R)
           # Una combinacion de Precision y  Recall en un solo valor (una especie de media)
# Accuracy: (TP+TN)/(TP+TN+FP+FN)
           # Funciona mal si las clases estan desbalanceadas
           # Ejemplo: 1000 datos: 950 son 1 y 50 son 0
           #          Nuestro modelo dice siempre 1, entonces el accuracy es 0.95. Pero el modelo es malo, porque no predice nada bien, simplemente dice 1
# Macro-average:
           # Se tiene en cuenta en clases balanceadas
# Micro-average:
           # Se tiene en cuenta en clases desbalanceadas

import signal
import csv
import getopt
import sys
import os
import pandas as pd
import csv
import time
#import datetime
#import ciso8601
# ciso8601.parse_datetime(ml_dataset[columna])
import numpy as np
from sklearn.model_selection import train_test_split
from imblearn.under_sampling import RandomUnderSampler
#from imblearn.over_sampling import RandomOverSampler
#from imblearn.over_sampling import SMOTE
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
#from sklearn.linear_model import LinearRegression
from sklearn.metrics import f1_score
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
#from sklearn.metrics import precision_score
#from sklearn.metrics import recall_score
#from sklearn.metrics import accuracy_score
import pickle
from preprocessor import Preprocessor

inputFile = None
excludedColumns = None
targetColumn = None
imputeOption = None
imputeOptions = ['MEAN', 'MEDIAN', 'MODE', 'CONSTANT']
algorithm = None
printStats = False
algorithms = ['knn', 'decision tree', 'random forest', 'naive bayes']
rescaleOption = None
rescaleOptions = ['MAX', 'MINMAX', 'Z-SCALE']
testSize = 0.2
randomState = None
kValues = None
wValues = None
dValues = None
max_depths = None
min_samples_splits = None
min_samples_leafs = None
outputModelName = None
evaluation = None

def signal_handler(sig_num, frame):
    print("[!] Saliendo del programa...")
    sys.exit(1)

def helpPanel():
    #python crearModelo.py -a 0 1,5 1,2 uniform,distance -f iris.csv -i mode -t Especie -s -o modelo.pkl
    #python crearModelo.py -a 1 -f iris.csv -i mode -t Especie -s
    #-i CONSTANT 10 --> imputeValue = 10
    #-i <file> --> por cada columna
    #Defaults: testSize=0.2
    print()
    print("\tHelp")
    print("\t----")
    print("\tUsage: python crearModelo.py -f <input-dataset> -t <target-column> -a <algorithm-num>  --impute-method <mehtod> [optional-args]")
    print()
    print("\tArguments")
    print("\t---------")
    print('\t-o|--ouput <outputFile>\t\t\tOutput name for the model (ex: model.pkl)')
    print('\t-f|--file <inputFile>\t\t\tInput csv dataset file')
    print('\t-e|--exclude <excludeHeaders>\t\tcoma separated list to exclude columns')
    print('\t-t|--target <target column header>\tTarget column header name')
    print('\t-s|--stats \t\t\t\tPrint trained model stats')
    print('\t-a|--algorithm <number>\t\t\tSelect the algorithm to use')
    print('\t\t\t\t\t\t\t0: knn (-a 0 <k> <d> <w>)')
    print('\t\t\t\t\t\t\t\tk=[k1,k2,k3,...|kmin:kmax] odd numbers') 
    print('\t\t\t\t\t\t\t\td=[1,2]')
    print('\t\t\t\t\t\t\t\tw=[unform,distance]')
    print('\t\t\t\t\t\t\t1: decision tree (-a 1 <max_depth> <min_samples_split> <min_samples_leaf>)')
    print('\t\t\t\t\t\t\t\tmax_depth=[d1,d2,d3...|dmin:dmax] any numbers')
    print('\t\t\t\t\t\t\t\tmin_samples_split=[1,2]')
    print('\t\t\t\t\t\t\t\tmin_samples_leaf=[1,2]')
    #print('\t\t\t\t\t\t\t2: random forest')
    print('\t-h|--help \t\t\t\tPrint this help panel')
    print('\t-i|--impute <name>\t\t\tChoose impute method (filename,MEAN,MEDIAN,MODE,CONSTANT <n>)')
    print('\t\t\t\t\t\t\tfilename: file containing impute method for each column splicitly')
    print('\t\t\t\t\t\t\tOTHER: one same impute method for all columns')
    print('\t-r|--rescale <name>\t\t\tChoose rescale method (filename,MAX,MINMAX,Z-SCALE)')
    print('\t\t\t\t\t\t\tfilename: file containing rescale method for each column splicitly')
    print('\t\t\t\t\t\t\tOTHER: one same rescale method for all columns')
    print('\t--random-state <int>\t\t\tSeed to separate train and test dataset the same way')
    print('\t--test-size <float>\t\t\tChoose the test size')
    print()
    print('\tDefaults')
    print('\t--------')
    print('\toutput model: False')
    print('\tprint stats: False')
    print('\ttest size: 0.2')
    print('\timpute method: None (do not impute any value)')
    print('\trescale method: None (do not rescale the dataset)')
    print()
    print('\tExamples')
    print('\t--------')
    print('\t$ python crearModelo.py -f iris.csv -a 0 1,3,5 1,2 uniform,distance -i MODE -t Especie -s -o model.pkl')
    print('\t\t12 convinations of hyperparameters for knn')
    print('\t\timpute MODE for all columns')
    print('\t\ttarget column "Especie"')
    print('\t\tprint model stats')
    print('\t\toutput model "model.pkl"')
    print('\t$ python crearModelo.py -f iris.csv -a 0 1,7 2 distance -e -i impute.csv -r rescale.csv -t Especie -e Ancho de sepalo,Largo de petalo -o model.pkl')
    print('\t\t2 convinations of hyperparameters for knn')
    print('\t\timpute with file for all columns')
    print('\t\trescale with file for all columns')
    print('\t\ttarget column "Especie"')
    print('\t\tdo not take into account columns "Ancho de sepalo" and "Largo de petalo" to train the model')
    print('\t\tdo not print model stats')
    print('\t\toutput model "model.pkl"')
    print()
    print('\tImpute file:')
    print('\t\tcol1,MODE')
    print('\t\tcol2,MEAN')
    print('\t\tcol3,CONSTANT,3')
    print()
    print('\tRescale file:')
    print('\t\tcol1,MINMAX')
    print('\t\tcol2,Z-SCALE')
    print('\t\tcol3,MAX')
    print()

def comprobarArgumentosEntradaObligatorios():
    global imputeOption
    global kValues
    global dValues
    global wValues
    global max_depths
    global min_samples_splits
    global min_samples_leafs
    error = False
    if inputFile == None or not os.path.exists(inputFile):
        print("[!] Error: Especifica cual es el fichero que contiene los datos.")
        error = True
    if targetColumn == None:
        print("[!] Error: Especifica cual es la columna objetivo.")
        error = True
    if imputeOption == None:
        print("[!] Error: Especifica cual es el metodo de imputacion")
        error = True
    if algorithm == None:
        print("[!] Error: Especifica cual es el algoritmo que quieres usar para hacer el modelo")
        error = True
    if imputeOption == 'CONSTANT':
        shift = 1
        for i,value in enumerate(sys.argv[1:]):
            if value.upper() == 'CONSTANT':
                const = sys.argv[1:][i+shift]
                try:
                    if not const in remainder:
                        int('Throw error')
                    const = float(sys.argv[1:][i+shift])
                    imputeOption = f'{str(value.upper())},{str(const)}'
                except:
                    print('[!] CONSTANT only supports integer values')
                    sys.exit(1)
    shift = 2
    error = False
    for i,value in enumerate(sys.argv[1:]):
        if value in ['-a', '--algorithm']:
            values = sys.argv[1:][i+shift:i+shift+3]
            for value in values:
                if value not in remainder:
                    error = True
            if not error:
                if algorithms[algorithm] == 'knn':
                    kValues = []
                    try:
                        if values[0].find(':') != -1:
                            maxMinValues = values[0].split(':')
                            kValues = [i for i in range(int(maxMinValues[0]),int(maxMinValues[1])+2,2)]
                        else:
                            kValues = [int(i) for i in values[0].split(',')]
                    except:
                        print('[!] Rango mal especificado para el barrido de hyperparametros k del knn')
                        sys.exit(1)
                    dValues = [int(i) for i in values[1].split(',')]
                    wValues = [str(i) for i in values[2].split(',')]
                elif algorithms[algorithm] == 'decision tree':
                    max_depths = []
                    try:
                        if values[0].find(':') != -1:
                            maxMinValues = values[0].split(':')
                            max_depths = [i for i in range(int(maxMinValues[0]),int(maxMinValues[1])+1,1)]
                        else:
                            max_depths = [int(i) for i in values[0].split(',')]
                    except:
                        print('[!] Rango mal especificado para el barrido de hyperparametros max_depth del decision tree')
                        sys.exit(1)
                    min_samples_splits = [int(i) for i in values[1].split(',')]
                    min_samples_leafs = [int(i) for i in values[2].split(',')]
            else:
                if algorithms[algorithm] == 'knn':
                    print('[!] Indica bien los argumentos del algoritmo knn')
                    sys.exit(1)
                elif algorithms[algorithm] == 'decision tree':
                    print('[!] Indica bien los argumentos del algoritmo decision tree')
                    sys.exit(1)
    if error:
        helpPanel()
        sys.exit(1)

def cargarDataset(pInputFile):
    ml_dataset = None
    with open(inputFile, 'r') as csvFile:
        primerosDatos = csv.Sniffer().sniff(csvFile.read(1024)) #Leer los primero 1024 bytes del fichero
        csvFile.seek(0) # Regresa al inicio del archivo
        lector = csv.reader(csvFile, primerosDatos, delimiter=',')
        tiene_header = csv.Sniffer().has_header(csvFile.read(1024)) # Detecta si el archivo tiene encabezado
        if tiene_header: #Si tiene header se carga directamente
            ml_dataset = pd.read_csv(inputFile, low_memory=False)
        else: #Si no tiene header se añade uno por defecto
            csvFile.seek(0)
            num_cols = len(csvFile.readline().split(','))
            headers = []
            for i in range(1,num_cols+1):
                headers.append("col"+str(i))
            ml_dataset = pd.read_csv(inputFile, names=headers, header=None, low_memory=False)
    return ml_dataset

def crearModelo(pml_dataset, palgorithm, ptarget_map):
    if randomState != None:
        train, test = train_test_split(pml_dataset,test_size=testSize,random_state=randomState,stratify=pml_dataset[targetColumn])
    else:
        train, test = train_test_split(pml_dataset,test_size=testSize,stratify=pml_dataset[targetColumn])
    
    trainX = train.drop(targetColumn, axis=1) #train dataset de datos sin target
    testX = test.drop(targetColumn, axis=1) #test dataset sin target
    trainY = np.array(train[targetColumn]) #train columna target
    testY = np.array(test[targetColumn]) #test columna target
    if len(ptarget_map) == 2:
        sampler = RandomUnderSampler(sampling_strategy=0.5) #Coge el 50% de las muestras de la clase mayoritaria para balancear ambas clases
        #TODO: oversample
    elif len(ptarget_map) >= 3:
        sampler = RandomUnderSampler()
        #smote = SMOTE()
        #trainX, trainY = smote.fit_resample(trainX, trainY)
        #TODO: oversample
    trainX, trainY = sampler.fit_resample(trainX,trainY)
    testX, testY = sampler.fit_resample(testX, testY)
    
    modelos = []
    if algorithms[palgorithm] == 'knn':
        fScoreAverage = evaluation
        for k in kValues:
            for d in dValues:
                for w in wValues:
                    clf = KNeighborsClassifier(n_neighbors=k,
                        weights=w,
                        algorithm='auto',
                        leaf_size=30,
                        p=d)
                    clf.class_weight = "balanced"
                    clf.fit(trainX, trainY)
                    predictions = clf.predict(testX)
                    fScore = f1_score(testY, predictions, average=fScoreAverage)
                    reporte = classification_report(testY,predictions)
                    fScore = f1_score(testY, predictions, average=fScoreAverage)
                    matriz_confusion = confusion_matrix(testY, predictions, labels=[1,0])
                    probas = clf.predict_proba(testX)
                    predictions = pd.Series(data=predictions, index=testX.index, name='predicted_value')
                    cols = [
                        u'probability_of_value_%s' % label
                        for (_, label) in sorted([(int(ptarget_map[label]), label) for label in ptarget_map])
                    ]
                    probabilities = pd.DataFrame(data=probas, index=testX.index, columns=cols)
                    modelos.append([clf,fScore,reporte,{'k': k, 'w': w, 'd': d}])
    elif algorithms[palgorithm] == 'decision tree':
        fScoreAverage = 'weighted'
        for max_depth in max_depths:
            for min_samples_split in min_samples_splits:
                for min_samples_leaf in min_samples_leafs:
                    clf = DecisionTreeClassifier(
                        max_depth = max_depth,
                        min_samples_split = min_samples_split,
                        min_samples_leaf = min_samples_leaf
                    )
                    clf.class_weight = "balanced"
                    clf.fit(trainX, trainY)
                    predictions = clf.predict(testX)        
                    fScore = f1_score(testY, predictions, average=fScoreAverage)
                    reporte = classification_report(testY,predictions)
                    #matriz_confusion = confusion_matrix(testY, predictions, labels=[1,0])
                    modelos.append([clf,fScore,reporte,{'max_depth': max_depth, 'min_samples_split': min_samples_split, 'min_samples_leaf': min_samples_leaf}])
                    #probas = clf.predict_proba(testX)
                    #predictions = pd.Series(data=predictions, index=testX.index, name='predicted_value')
                    #cols = [
                    #    u'probability_of_value_%s' % label
                    #    for (_, label) in sorted([(int(ptarget_map[label]), label) for label in ptarget_map])
                    #]
                    #probabilities = pd.DataFrame(data=probas, index=testX.index, columns=cols)

                    # Build scored dataset
                    #results_test = testX.join(predictions, how='left')
                    #results_test = results_test.join(probabilities, how='left')
                    #results_test = results_test.join(test[targetColumn], how='left')
                    #results_test = results_test.rename(columns= {targetColumn: 'TARGET'})
                    #print(results_test)
    ml_model = None
    fScoreBest = 0
    #modelargs = 
    for modelo in modelos:
        if modelo[1] >= fScoreBest:
            ml_model = modelo
            fScoreBest = modelo[1]
    return ml_model

if __name__ == '__main__':
    # Gestionar las senales de teclado durante la ejecucion
    signal.signal(signal.SIGINT, signal_handler)

    # Definir argumentos de entrada
    input_args = sys.argv[1:]
    short_opts = "f:e:t:hi:a:sr:o:m:"
    long_opts = ['file=', 'exclude=', 'target=', 'help', 'impute=', 'algorithm=', 'stats', 'rescale=', 'test-size=', 'random-state=', 'output=']
    
    # Parsear los argumentos y sus valores
    try:
        # En options se guarda [opt,arg] por cada argumento
        # En reminder se guardan los argumentos sobrantes: -o 1 2 (options=['-o',1],reminder=[2])
        options,remainder = getopt.gnu_getopt(input_args,short_opts,long_opts)
    except getopt.GetoptError as err:
        print('[!] ERROR: The arguments given does not meet the requirements')
        helpPanel()
        sys.exit(1)
    
    # Cargar los valores de los argumentos de entrada
    for opt,arg in options:
        if opt in ('-f', '--file'):
            inputFile = arg
            if not os.path.exists(inputFile):
                print("[!] Error: El fichero de los datos de entrada no existe.")
                sys.exit(1)
        elif opt in ('-e', '--exclude'):
            excludedColumns = arg
        elif opt in ('-t', '--target'):
            targetColumn = arg
        elif opt in ('-h','--help'):
            helpPanel()
            exit(0)
        elif opt in ('-i', '--impute'):
            if arg.upper() in imputeOptions: # Comprobar que es MEAN, MEDIAN, MODE o CONSTANT
                imputeOption = arg.upper()
            elif not os.path.exists(arg): # Si es un fichero, comprobar que existe
                print("[!] Error: El metodo de imputacion no es correcto o el fichero no existe.")
                sys.exit(1)
        elif opt in ('-a', '--algorithm'):
            try:
                algorithm = int(arg)
            except:
                print('[!] The algorithm selection must be an integer')
                sys.exit(1)
                
            if algorithm >= len(algorithms) or algorithm < 0:
                print('[!] The algorithm selection is out of range, choose a valid one')
                sys.exit(1)
        elif opt in ('-s', '--stats'):
            printStats = True
        elif opt in ('-r', '--rescale'):
            if arg.upper() in rescaleOptions:
                rescaleOption = arg.upper()
            elif not os.path.exists(arg):
                print("[!] Error: El metodo de rescalado no es correcto o el fichero no existe.")
                sys.exit(1)
        elif opt == '--test-size':
            arg = str(arg)
            try:
                testSize = float(arg)
                if testSize <= 0 or testSize >= 1:
                    int('throw error')
            except:
                print('[!] The test size must be a float between 0.0 and 1.0')
                sys.exit(1)
        elif opt == '--random-state': #Random state se usa como semilla para separar train y test de la misma forma, sirve para que un experimento sea reproducible, si no se le da ningun valor, sera aleatorio
            arg = str(arg) #Convertirlo a string para comprobar correctamente si es un float o int
            try:
                #int(2) --> 2
                #int(str(2)) --> 2
                #int(1.2) --> 1
                #int(str(1.2)) --> error
                randomState = int(arg)
            except:
                print('[!] Random state must be an integer')
                sys.exit(1)
        elif opt in ('-o', '--output'):
            outputModelName = arg
        elif opt == '-m':
            evaluation = arg
    
    # Comprobar que los argumentos de entrada requeridos se han especificado en la llamada
    comprobarArgumentosEntradaObligatorios()
    
    # Cargar el fichero de datos en un dataset de pandas
    ml_dataset = cargarDataset(inputFile)

    #print(f'{targetColumn}, {algorithms[algorithm]}, {excludedColumns}, {imputeOption}, {rescaleOption}')
    preprocessor = Preprocessor()
    ml_dataset,target_map = preprocessor.preprocessDataset(ml_dataset, targetColumn, algorithms[algorithm], excludedColumns, imputeOption, rescaleOption)

    ml_model = crearModelo(ml_dataset, algorithm, target_map)

    if printStats: #clf,fScore,reporte,{k: k, w: w, d: d}
        if len(ml_model) == 4:
            print('\n\tEstadisticas para el mejor modelo entrenado')
            print('\t-------------------------------------------')
            print()
            for hyperparam in ml_model[3]:
                print(f'\t{hyperparam}={ml_model[3][hyperparam]}')
            print()
            print(ml_model[2])
    
    if outputModelName != None:
        pickle.dump(ml_model[0], open(outputModelName, 'wb'))
        #print('TODO: exportar el mejor modelo entrenado de todo el for')
    
    