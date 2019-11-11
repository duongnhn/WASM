// Case 3: Fibonacci
// fib(i0) {if (i0 < 2) return i0; return fib(i-1)+fib(i-2)};
load("test/mjsunit/wasm/wasm-module-builder.js");
const builder = new WasmModuleBuilder();
builder.addFunction('fib', kSig_i_i)
    .addBody([
      kExprLocalGet, 0,
      kExprLocalGet, 0,
      kExprI32Const, 2,
      kExprI32LeS,  // i < 2 ?
      kExprBrIf, 0, // --> return i
      kExprI32Const, 1, kExprI32Sub,  // i - 1
      kExprCallFunction, 0, // fib(i - 1)
      kExprLocalGet, 0, kExprI32Const, 2, kExprI32Sub,  // i - 2
      kExprCallFunction, 0, // fib(i - 2)
      kExprI32Add
    ])
    .exportFunc();
const instance = builder.instantiate();
const f = instance.exports.fib;

const iteration = 10;
var t0 = performance.now();
console.log("start");
for (let i=0;i<iteration;i++) {
  var x = f(30);
}
console.log("end");
var t1 = performance.now();
console.log("Call to doSomething took " + (t1 - t0)/iteration + " milliseconds.");
