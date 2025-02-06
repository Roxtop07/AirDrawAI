import speech_recognition as sr
import nltk
import numpy as np
import tensorflow as tf
from nltk.tokenize import word_tokenize
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense

# Download the punkt tokenizer for word tokenization
nltk.download('punkt')

# Sample dataset for intent classification
intents = {
    "greetings": ["hello", "hi", "good morning", "good evening"],
    "turn_on_light": ["turn on the light", "lights on", "open the lights"],
    "play_music": ["play music", "play a song", "start the music"]
}

# Preparing the training data
sentences = []
labels = []
class_labels = []

for intent, phrases in intents.items():
    for phrase in phrases:
        sentences.append(phrase)
        labels.append(intent)

# Tokenizing sentences
words = []
for sentence in sentences:
    word_list = word_tokenize(sentence)
    words.extend(word_list)

words = sorted(set(words))  # Remove duplicates and sort
word_indices = {word: idx for idx, word in enumerate(words)}

# Convert sentences to bag-of-words representation
X_train = []
for sentence in sentences:
    bag = [0] * len(words)
    for word in word_tokenize(sentence):
        if word in word_indices:
            bag[word_indices[word]] = 1
    X_train.append(bag)

# Encode the labels
label_encoder = LabelEncoder()
y_train = label_encoder.fit_transform(labels)

# Build the model
model = Sequential()
model.add(Dense(128, input_dim=len(words), activation='relu'))
model.add(Dense(64, activation='relu'))
model.add(Dense(len(intents), activation='softmax'))

model.compile(loss='sparse_categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

# Train the model
model.fit(np.array(X_train), np.array(y_train), epochs=200)

# Save the model
model.save('intent_recognition_model.h5')

# Function for speech recognition
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Adjusting for ambient noise... Please wait.")
        recognizer.adjust_for_ambient_noise(source)  # Adjust for ambient noise
        print("Listening for your command...")
        audio = recognizer.listen(source)

        try:
            print("Recognizing...")
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            print("Sorry, I could not understand the audio.")
            return None
        except sr.RequestError as e:
            print(f"Error with the speech recognition service: {e}")
            return None

# Function to classify intent from text
def classify_intent(text):
    # Convert the text to bag-of-words
    bag = [0] * len(words)
    for word in word_tokenize(text):
        if word in word_indices:
            bag[word_indices[word]] = 1

    # Predict intent
    prediction = model.predict(np.array([bag]))  # Use the trained model
    predicted_class = np.argmax(prediction)
    intent = label_encoder.inverse_transform([predicted_class])[0]
    return intent

# Main function
if __name__ == "__main__":
    command = recognize_speech()
    if command:
        intent = classify_intent(command)
        print(f"Intent recognized: {intent}")
