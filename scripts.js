// with return keywords

function add(a, b) {
    return a + b;
}   
console.log(add(5, 3)); // Outputs: 8

// withput return keywords

function multiply(a, b) {
    a * b;
}
console.log(multiply(5, 3)); // Outputs: undefined
// because there is no return statement
// The function performs the multiplication but does not return the result.
// To get the result, we need to add a return statement 
// like in the add function above.
// Without the return statement, the function's output is undefined.
// This demonstrates the importance of the return keyword in functions.
// It allows functions to send back results to the caller.
// In summary, always use return in functions when you want to get a result back.
// Otherwise, the function will return undefined by default.    
// This is a common mistake for beginners in programming.
// Always remember to include return statements as needed.

// Example of a function without return statement           
function greet(name) {
    console.log("Hello, " + name + "!");
}   
greet("Alice"); // Outputs: Hello, Alice!           

// Example of a function with return statement
function square(num) {
    return num * num;
}   
console.log(square(4)); // Outputs: 16
// The square function returns the square of the input number.
// This allows us to use the result in further calculations or display it.
// In contrast, the greet function only prints a message and does not return anything.
// This highlights the difference between functions that return values and those that do not.       

// Always consider whether you need a return value when defining functions.
// This will help you avoid unexpected undefined results in your code.
// Proper use of return statements enhances code functionality and usability.
// In conclusion, remember:
