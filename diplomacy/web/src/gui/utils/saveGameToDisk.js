export function saveGameToDisk(game, onError) {
    if (game.client) {
        game.client.save()
            .then((savedData) => {
                const domLink = document.createElement('a');
                domLink.setAttribute(
                    'href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(JSON.stringify(savedData)));
                domLink.setAttribute('download', `${game.game_id}.json`);
                domLink.style.display = 'none';
                document.body.appendChild(domLink);
                domLink.click();
                document.body.removeChild(domLink);
            })
            .catch(exc => onError(`Error while saving game: ${exc.toString()}`));
    } else {
        onError(`Cannot save this game.`);
    }
}
