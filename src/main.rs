#![deny(unsafe_code)]

#[cfg(target_arch = "wasm32")]
use wasm_bindgen::prelude::*;

slint::include_modules!();

pub fn main() {
    let main_window = MainWindow::new().unwrap();

    main_window.run().unwrap();
}