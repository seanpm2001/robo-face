#![deny(unsafe_code)]

use futures_util::StreamExt;
use rand::prelude::*;
use std::sync::Arc;
use tokio::sync::mpsc;
use tokio::sync::mpsc::UnboundedSender;
use tokio::sync::RwLock;
use tokio_stream::wrappers::UnboundedReceiverStream;
use warp::ws::Message;
use warp::Filter;

slint::include_modules!();

pub fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut rng = rand::thread_rng();

    let main_window = MainWindow::new()?;

    let main_window_weak = main_window.as_weak();
    std::thread::spawn(move || {
        tokio::runtime::Runtime::new()
            .unwrap()
            .block_on(robot_server(main_window_weak))
            .unwrap();
    });

    let main_window_weak = main_window.as_weak();
    let random_emotion_timer = slint::Timer::default();
    random_emotion_timer.start(
        slint::TimerMode::Repeated,
        std::time::Duration::from_secs(3),
        move || {
            let main_window = main_window_weak.unwrap();
            let _telemetry = main_window.get_telemetry();
            let random_emotion: f32 = rng.gen();
            let new_state = if random_emotion < 0.5 {
                FaceState::Neutral
            } else if random_emotion < 0.6 {
                FaceState::Suspicious
            } else if random_emotion < 0.8 {
                FaceState::Happy
            } else {
                FaceState::Bored
            };

            main_window.set_face_state(new_state);
        },
    );

    main_window.run()?;

    Ok(())
}

async fn robot_server(main_window: slint::Weak<MainWindow>) -> tokio::io::Result<()> {
    let (ui_channel_write, ui_channel_read) = mpsc::unbounded_channel::<Message>();

    std::thread::spawn(move || {
        tokio::runtime::Runtime::new()
            .unwrap()
            .block_on(async move {
                let mut ui_channel_read = UnboundedReceiverStream::new(ui_channel_read);
                while let Some(message) = ui_channel_read.next().await {
                    let Ok(str) = message.to_str() else {
                        eprintln!("Received binary websocket message. Protocol error?");
                        continue;
                    };
                    eprintln!("UI message: {}", str);
                    match serde_json::from_str::<Telemetry>(str) {
                        Ok(telemetry) => {
                            main_window
                                .upgrade_in_event_loop(move |main_window| {
                                    let angle = telemetry.cg_angle;
                                    if (angle > -8.) && (angle < -6.) || (angle > -2.) && angle < 0.
                                    {
                                        // Small push
                                        main_window.set_face_state(FaceState::Suspicious);
                                    } else if (angle < -8.) || (angle > 0.) {
                                        // Big push
                                        main_window.set_face_state(FaceState::Angry);
                                    }

                                    main_window.set_telemetry(telemetry);
                                })
                                .unwrap();
                        }
                        Err(e) => {
                            eprintln!("error parsing telemetry message: {e}");
                        }
                    }
                }
            });
    });

    let ui_channel_write = Arc::new(RwLock::new(ui_channel_write));

    let server = warp::path::end()
        .and(warp::ws())
        .and(warp::any().map(move || ui_channel_write.clone()))
        .map(|ws: warp::ws::Ws, ui_channel_write| {
            ws.on_upgrade(move |socket| handle_robot(socket, ui_channel_write))
        });

    warp::serve(server).run(([0, 0, 0, 0], 8000)).await;

    Ok(())
}

async fn handle_robot(ws: warp::ws::WebSocket, ui_channel: Arc<RwLock<UnboundedSender<Message>>>) {
    let (_websocket_write, mut websocket_read) = ws.split();

    while let Some(result) = websocket_read.next().await {
        let message = match result {
            Ok(message) => message,
            Err(e) => {
                eprintln!("websocket error: {e}");
                break;
            }
        };
        ui_channel.write().await.send(message).unwrap();
    }
}
